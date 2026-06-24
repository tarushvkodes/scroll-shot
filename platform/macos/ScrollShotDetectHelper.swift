import ApplicationServices
import AppKit
import Foundation

struct Candidate {
    let role: String
    let title: String
    let x: Double
    let y: Double
    let width: Double
    let height: Double
    let score: Double
}

let useMousePoint = CommandLine.arguments.contains("--mouse")

func attr(_ element: AXUIElement, _ name: String) -> AnyObject? {
    var value: AnyObject?
    let result = AXUIElementCopyAttributeValue(element, name as CFString, &value)
    return result == .success ? value : nil
}

func stringAttr(_ element: AXUIElement, _ name: String) -> String {
    return attr(element, name) as? String ?? ""
}

func rectFor(_ element: AXUIElement) -> CGRect? {
    guard
        let posObject = attr(element, kAXPositionAttribute),
        let sizeObject = attr(element, kAXSizeAttribute)
    else {
        return nil
    }
    let posValue = posObject as! AXValue
    let sizeValue = sizeObject as! AXValue
    var point = CGPoint.zero
    var size = CGSize.zero
    guard AXValueGetValue(posValue, .cgPoint, &point),
          AXValueGetValue(sizeValue, .cgSize, &size) else {
        return nil
    }
    return CGRect(origin: point, size: size)
}

func childrenOf(_ element: AXUIElement) -> [AXUIElement] {
    var names: CFArray?
    AXUIElementCopyAttributeNames(element, &names)
    let available = (names as? [String]) ?? []
    var children: [AXUIElement] = []
    for key in [kAXChildrenAttribute as String, kAXVisibleChildrenAttribute as String] {
        if !available.contains(key) {
            continue
        }
        if let value = attr(element, key) {
            if let list = value as? [AXUIElement] {
                children.append(contentsOf: list)
            } else if CFGetTypeID(value) == AXUIElementGetTypeID() {
                children.append(value as! AXUIElement)
            }
        }
    }
    return children
}

func parentOf(_ element: AXUIElement) -> AXUIElement? {
    guard let value = attr(element, kAXParentAttribute), CFGetTypeID(value) == AXUIElementGetTypeID() else {
        return nil
    }
    return (value as! AXUIElement)
}

func hasAttribute(_ element: AXUIElement, _ name: String) -> Bool {
    var names: CFArray?
    AXUIElementCopyAttributeNames(element, &names)
    return ((names as? [String]) ?? []).contains(name)
}

func scoreCandidate(role: String, rect: CGRect, window: CGRect, hasVerticalScrollBar: Bool) -> Double {
    if rect.width < 120 || rect.height < 120 {
        return -1
    }
    let windowArea = max(1.0, window.width * window.height)
    let area = rect.width * rect.height
    let areaRatio = min(area / windowArea, 1.0)
    let roles: [String: Double] = [
        "AXScrollArea": 120,
        "AXWebArea": 95,
        "AXTextArea": 90,
        "AXTable": 80,
        "AXOutline": 75,
        "AXList": 75,
        "AXGroup": 28,
        "AXSplitterGroup": 20
    ]
    var score = roles[role] ?? 0
    if hasVerticalScrollBar {
        score += 100
    }
    score += areaRatio * 55
    if rect.height > window.height * 0.45 {
        score += 20
    }
    if rect.width > window.width * 0.35 {
        score += 12
    }
    if rect.width >= window.width * 0.96 && rect.height >= window.height * 0.96 {
        score -= 80
    }
    return score
}

func contains(_ rect: CGRect, _ point: CGPoint) -> Bool {
    return point.x >= rect.minX && point.x <= rect.maxX && point.y >= rect.minY && point.y <= rect.maxY
}

func scorePointCandidate(role: String, rect: CGRect, window: CGRect, hasVerticalScrollBar: Bool) -> Double {
    var score = scoreCandidate(role: role, rect: rect, window: window, hasVerticalScrollBar: hasVerticalScrollBar)
    if score < 0 {
        return score
    }
    let windowArea = max(1.0, window.width * window.height)
    let areaRatio = min((rect.width * rect.height) / windowArea, 1.0)
    score += (1.0 - areaRatio) * 90
    if areaRatio > 0.90 {
        score -= 110
    }
    return score
}

func walk(_ element: AXUIElement, windowRect: CGRect, depth: Int, candidates: inout [Candidate]) {
    if depth > 12 {
        return
    }
    let role = stringAttr(element, kAXRoleAttribute)
    if let rect = rectFor(element) {
        let hasScroll = hasAttribute(element, kAXVerticalScrollBarAttribute)
        let score = scoreCandidate(role: role, rect: rect, window: windowRect, hasVerticalScrollBar: hasScroll)
        if score > 0 {
            candidates.append(Candidate(
                role: role,
                title: stringAttr(element, kAXTitleAttribute),
                x: rect.origin.x,
                y: rect.origin.y,
                width: rect.width,
                height: rect.height,
                score: score
            ))
        }
    }
    for child in childrenOf(element) {
        walk(child, windowRect: windowRect, depth: depth + 1, candidates: &candidates)
    }
}

func walkContainingPoint(_ element: AXUIElement, windowRect: CGRect, point: CGPoint, depth: Int, candidates: inout [Candidate]) {
    if depth > 14 {
        return
    }
    let role = stringAttr(element, kAXRoleAttribute)
    if let rect = rectFor(element), contains(rect, point) {
        let hasScroll = hasAttribute(element, kAXVerticalScrollBarAttribute)
        let score = scorePointCandidate(role: role, rect: rect, window: windowRect, hasVerticalScrollBar: hasScroll)
        if score > 0 {
            candidates.append(Candidate(
                role: role,
                title: stringAttr(element, kAXTitleAttribute),
                x: rect.origin.x,
                y: rect.origin.y,
                width: rect.width,
                height: rect.height,
                score: score
            ))
        }
        for child in childrenOf(element) {
            walkContainingPoint(child, windowRect: windowRect, point: point, depth: depth + 1, candidates: &candidates)
        }
    }
}

guard AXIsProcessTrusted() else {
    FileHandle.standardError.write("Accessibility permission is required for automatic scroll target detection.\n".data(using: .utf8)!)
    exit(3)
}

guard let app = NSWorkspace.shared.frontmostApplication else {
    FileHandle.standardError.write("Could not find frontmost application.\n".data(using: .utf8)!)
    exit(2)
}

let appElement = AXUIElementCreateApplication(app.processIdentifier)
let focused = attr(appElement, kAXFocusedWindowAttribute)
let window: AXUIElement?
if focused != nil && CFGetTypeID(focused!) == AXUIElementGetTypeID() {
    window = (focused as! AXUIElement)
} else if let windows = attr(appElement, kAXWindowsAttribute) as? [AXUIElement] {
    window = windows.first
} else {
    window = nil
}

guard let targetWindow = window, let windowRect = rectFor(targetWindow) else {
    FileHandle.standardError.write("Could not inspect the frontmost window.\n".data(using: .utf8)!)
    exit(2)
}

var candidates: [Candidate] = []
if useMousePoint {
    guard let mouse = CGEvent(source: nil)?.location else {
        FileHandle.standardError.write("Could not read mouse location.\n".data(using: .utf8)!)
        exit(2)
    }
    walkContainingPoint(targetWindow, windowRect: windowRect, point: mouse, depth: 0, candidates: &candidates)
    if candidates.isEmpty {
        let system = AXUIElementCreateSystemWide()
        var hitObject: AXUIElement?
        let hitResult = AXUIElementCopyElementAtPosition(system, Float(mouse.x), Float(mouse.y), &hitObject)
        if hitResult == .success, let hit = hitObject {
            var chain: [AXUIElement] = []
            var current: AXUIElement? = hit
            while let element = current, chain.count < 16 {
                chain.append(element)
                current = parentOf(element)
            }
            let rects = chain.compactMap { rectFor($0) }
            let containerRect = rects.max(by: { ($0.width * $0.height) < ($1.width * $1.height) }) ?? windowRect
            for element in chain {
                guard let rect = rectFor(element), contains(rect, mouse) else {
                    continue
                }
                let role = stringAttr(element, kAXRoleAttribute)
                let hasScroll = hasAttribute(element, kAXVerticalScrollBarAttribute)
                let score = scorePointCandidate(role: role, rect: rect, window: containerRect, hasVerticalScrollBar: hasScroll)
                if score > 0 {
                    candidates.append(Candidate(
                        role: role,
                        title: stringAttr(element, kAXTitleAttribute),
                        x: rect.origin.x,
                        y: rect.origin.y,
                        width: rect.width,
                        height: rect.height,
                        score: score
                    ))
                }
            }
        }
    }
} else {
    walk(targetWindow, windowRect: windowRect, depth: 0, candidates: &candidates)
}

guard let best = candidates.sorted(by: { $0.score > $1.score }).first else {
    FileHandle.standardError.write("No likely scrollable region found in the frontmost window.\n".data(using: .utf8)!)
    exit(4)
}

let payload: [String: Any] = [
    "app": app.localizedName ?? "",
    "role": best.role,
    "title": best.title,
    "x": Int(best.x.rounded()),
    "y": Int(best.y.rounded()),
    "width": Int(best.width.rounded()),
    "height": Int(best.height.rounded()),
    "score": best.score
]
let data = try JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys])
print(String(data: data, encoding: .utf8)!)
