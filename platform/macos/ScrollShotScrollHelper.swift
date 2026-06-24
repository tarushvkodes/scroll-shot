import CoreGraphics
import Foundation

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(2)
}

let args = CommandLine.arguments
if args.count < 4 {
    fail("usage: scrollshot-scroll <x> <y> <deltaY>")
}

guard let x = Double(args[1]), let y = Double(args[2]), let deltaY = Int32(args[3]) else {
    fail("invalid arguments")
}

let point = CGPoint(x: x, y: y)
if let move = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved, mouseCursorPosition: point, mouseButton: .left) {
    move.post(tap: .cghidEventTap)
}

usleep(30_000)

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
