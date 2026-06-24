import AppKit
import Foundation

let seconds = max(1, Int(CommandLine.arguments.dropFirst().first ?? "5") ?? 5)

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

let width: CGFloat = 480
let height: CGFloat = 150
let screen = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1200, height: 800)
let origin = NSPoint(
    x: screen.midX - width / 2,
    y: screen.maxY - height - 48
)

let panel = NSPanel(
    contentRect: NSRect(origin: origin, size: NSSize(width: width, height: height)),
    styleMask: [.borderless, .nonactivatingPanel],
    backing: .buffered,
    defer: false
)
panel.level = .floating
panel.isOpaque = false
panel.backgroundColor = .clear
panel.ignoresMouseEvents = true

let container = NSView(frame: NSRect(x: 0, y: 0, width: width, height: height))
container.wantsLayer = true
container.layer?.backgroundColor = NSColor(calibratedWhite: 0.06, alpha: 0.92).cgColor
container.layer?.cornerRadius = 18

let title = NSTextField(labelWithString: "Scroll Shot")
title.font = NSFont.boldSystemFont(ofSize: 22)
title.textColor = .white
title.alignment = .center
title.frame = NSRect(x: 24, y: 104, width: width - 48, height: 28)

let instruction = NSTextField(labelWithString: "Move your pointer over the area that should scroll")
instruction.font = NSFont.systemFont(ofSize: 16)
instruction.textColor = NSColor(calibratedWhite: 0.84, alpha: 1.0)
instruction.alignment = .center
instruction.frame = NSRect(x: 24, y: 72, width: width - 48, height: 24)

let count = NSTextField(labelWithString: "\(seconds)")
count.font = NSFont.boldSystemFont(ofSize: 42)
count.textColor = NSColor(calibratedRed: 0.27, green: 0.84, blue: 1.0, alpha: 1.0)
count.alignment = .center
count.frame = NSRect(x: 24, y: 18, width: width - 48, height: 48)

container.addSubview(title)
container.addSubview(instruction)
container.addSubview(count)
panel.contentView = container
panel.orderFrontRegardless()

var remaining = seconds
Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { timer in
    remaining -= 1
    if remaining <= 0 {
        timer.invalidate()
        panel.close()
        app.terminate(nil)
    } else {
        count.stringValue = "\(remaining)"
    }
}

app.run()
