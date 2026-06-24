import CoreGraphics
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(2)
}

let args = CommandLine.arguments
if args.count < 4 {
    fail("usage: scrollshot-scroll <x> <y> <deltaY> [ticks] [click]")
}

guard let x = Double(args[1]), let y = Double(args[2]), let deltaY = Int32(args[3]) else {
    fail("invalid arguments")
}
let ticks = args.count >= 5 ? max(1, Int(args[4]) ?? 1) : 1
let shouldClick = args.count >= 6 && args[5] == "click"

let point = CGPoint(x: x, y: y)
if let move = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point, mouseButton: .left) {
    move.post(tap: .cghidEventTap)
}

usleep(30_000)

if shouldClick {
    if let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left) {
        down.post(tap: .cghidEventTap)
    }
    usleep(20_000)
    if let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) {
        up.post(tap: .cghidEventTap)
    }
    usleep(80_000)
}

for _ in 0..<ticks {
    guard let event = CGEvent(
        scrollWheelEvent2Source: nil,
        units: .pixel,
        wheelCount: 1,
        wheel1: deltaY,
        wheel2: 0,
        wheel3: 0
    ) else {
        fail("could not create scroll event")
    }

    event.location = point
    event.post(tap: .cghidEventTap)
    usleep(20_000)
}
