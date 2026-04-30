#!/usr/bin/env swift

import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

struct Config {
    var input: String = ""
    var output: String = ""
    var logo: String = ""
    var logoHeightRatio: Double = 0.10
    var logoMaxHeightPx: Int? = nil
    var marginTopRatio: Double = 0.03
    var marginTopPx: Int? = nil
    var marginRightRatio: Double = 0.025
    var marginRightPx: Int? = nil
    var opacity: Double = 1.0
}

func fail(_ message: String) -> Never {
    fputs("\(message)\n", stderr)
    exit(1)
}

func parseArgs() -> Config {
    var config = Config()
    let args = Array(CommandLine.arguments.dropFirst())
    var index = 0

    while index < args.count {
        let arg = args[index]
        guard index + 1 < args.count else {
            fail("Missing value for argument: \(arg)")
        }
        let value = args[index + 1]
        switch arg {
        case "--input":
            config.input = value
        case "--output":
            config.output = value
        case "--logo":
            config.logo = value
        case "--logo-height-ratio":
            guard let parsed = Double(value), parsed > 0 else {
                fail("Invalid --logo-height-ratio: \(value)")
            }
            config.logoHeightRatio = parsed
        case "--logo-max-height-px":
            guard let parsed = Int(value) else {
                fail("Invalid --logo-max-height-px: \(value)")
            }
            config.logoMaxHeightPx = parsed > 0 ? parsed : nil
        case "--margin-top-ratio":
            guard let parsed = Double(value), parsed >= 0 else {
                fail("Invalid --margin-top-ratio: \(value)")
            }
            config.marginTopRatio = parsed
        case "--margin-top-px":
            guard let parsed = Int(value) else {
                fail("Invalid --margin-top-px: \(value)")
            }
            config.marginTopPx = parsed >= 0 ? parsed : nil
        case "--margin-right-ratio":
            guard let parsed = Double(value), parsed >= 0 else {
                fail("Invalid --margin-right-ratio: \(value)")
            }
            config.marginRightRatio = parsed
        case "--margin-right-px":
            guard let parsed = Int(value) else {
                fail("Invalid --margin-right-px: \(value)")
            }
            config.marginRightPx = parsed >= 0 ? parsed : nil
        case "--opacity":
            guard let parsed = Double(value), parsed >= 0, parsed <= 1 else {
                fail("Invalid --opacity: \(value)")
            }
            config.opacity = parsed
        default:
            fail("Unknown argument: \(arg)")
        }
        index += 2
    }

    guard !config.input.isEmpty else {
        fail("Missing required argument: --input")
    }
    guard !config.output.isEmpty else {
        fail("Missing required argument: --output")
    }
    guard !config.logo.isEmpty else {
        fail("Missing required argument: --logo")
    }

    return config
}

func loadImage(_ path: String) -> CGImage {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
        fail("Unable to open image: \(path)")
    }
    guard let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fail("Unable to decode image: \(path)")
    }
    return image
}

func writePNG(_ image: CGImage, to path: String) {
    let url = URL(fileURLWithPath: path)
    guard let destination = CGImageDestinationCreateWithURL(
        url as CFURL,
        UTType.png.identifier as CFString,
        1,
        nil
    ) else {
        fail("Unable to create output: \(path)")
    }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else {
        fail("Unable to write output: \(path)")
    }
}

let config = parseArgs()
let baseImage = loadImage(config.input)
let logoImage = loadImage(config.logo)

let baseWidth = baseImage.width
let baseHeight = baseImage.height

guard let context = CGContext(
    data: nil,
    width: baseWidth,
    height: baseHeight,
    bitsPerComponent: 8,
    bytesPerRow: 0,
    space: CGColorSpaceCreateDeviceRGB(),
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fail("Unable to create drawing context")
}

context.interpolationQuality = .high
context.draw(baseImage, in: CGRect(x: 0, y: 0, width: baseWidth, height: baseHeight))

let logoAspect = Double(logoImage.width) / Double(logoImage.height)
let ratioLogoHeight = max(1, Int(round(Double(baseHeight) * config.logoHeightRatio)))
let logoHeight = config.logoMaxHeightPx.map { min(ratioLogoHeight, $0) } ?? ratioLogoHeight
let logoWidth = max(1, Int(round(Double(logoHeight) * logoAspect)))
let marginTop = config.marginTopPx ?? Int(round(Double(baseHeight) * config.marginTopRatio))
let marginRight = config.marginRightPx ?? Int(round(Double(baseWidth) * config.marginRightRatio))
let originX = max(0, baseWidth - marginRight - logoWidth)
let originY = max(0, baseHeight - marginTop - logoHeight)

context.saveGState()
context.setAlpha(CGFloat(config.opacity))
context.draw(
    logoImage,
    in: CGRect(x: originX, y: originY, width: logoWidth, height: logoHeight)
)
context.restoreGState()

guard let composited = context.makeImage() else {
    fail("Unable to finalize composited image")
}

writePNG(composited, to: config.output)
