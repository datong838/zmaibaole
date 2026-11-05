// Public whole-window evidence only. No input events, authorization requests,
// browser interfaces, coordinates for targeting, or window activation.
import Foundation
import AppKit
import CoreGraphics
import ScreenCaptureKit
import ImageIO
import UniformTypeIdentifiers
import Darwin

struct CaptureError: Error, CustomStringConvertible {
    let description: String
    init(_ description: String) { self.description = description }
}
func need(_ condition: Bool, _ message: String) throws {
    if !condition { throw CaptureError(message) }
}
func emit(_ value: [String: Any]) {
    if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]),
       let text = String(data: data, encoding: .utf8) { print(text) }
}

@available(macOS 14.0, *)
func verifiedWindow(_ content: SCShareableContent, pid: pid_t, id: CGWindowID, title: String) throws -> SCWindow {
    let selected = content.windows.filter { $0.windowID == id }
    try need(selected.count == 1, "sck-explicit-window-not-unique")
    let window = selected[0]
    try need(window.owningApplication?.processID == pid && window.owningApplication?.bundleIdentifier == "com.google.Chrome", "sck-window-pid-bundle-mismatch")
    try need(window.title == title || window.title == title + " - Google Chrome", "sck-window-title-mismatch")
    try need(window.isOnScreen && window.windowLayer == 0, "sck-window-not-normal-onscreen")
    let executable = NSRunningApplication(processIdentifier: pid)?.executableURL?.path
    try need(executable?.hasSuffix("/Google Chrome.app/Contents/MacOS/Google Chrome") == true, "sck-main-process-executable-mismatch")
    return window
}

@main struct WindowCapture {
    @MainActor
    static func main() async {
        do {
            let a = CommandLine.arguments
            try need(a.count == 9 && a[1] == "--pid" && a[3] == "--window-id" && a[5] == "--title" && a[7] == "--out", "explicit-pid-window-title-output-required")
            guard let pid = Int32(a[2]), pid > 0, let windowID = UInt32(a[4]), windowID > 0 else { throw CaptureError("positive-pid-window-required") }
            let title = a[6], out = URL(fileURLWithPath: a[8])
            try need(a[8].hasPrefix("/") && out.pathExtension.lowercased() == "png" && !title.isEmpty, "absolute-png-output-title-required")
            if FileManager.default.fileExists(atPath: out.path) {
                let attributes = try FileManager.default.attributesOfItem(atPath: out.path)
                try need(attributes[.type] as? FileAttributeType == .typeRegular && (attributes[.size] as? NSNumber)?.intValue == 0, "output-not-empty-owned-temporary-file")
            }
            // A CLI must initialize AppKit's public WindowServer connection.
            // Prohibited activation policy prevents a Dock item or focus change.
            let application = NSApplication.shared
            application.setActivationPolicy(.prohibited)
            // Never call SCShareableContent or capture with unavailable consent.
            // CGRequestScreenCaptureAccess is deliberately not used.
            try need(CGPreflightScreenCaptureAccess(), "sck-screen-capture-access-unavailable-no-permission-requested")
            guard #available(macOS 14.0, *) else { throw CaptureError("sck-screenshot-requires-macos14") }
            let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            let window = try verifiedWindow(content, pid: pid, id: windowID, title: title)
            let filter = SCContentFilter(desktopIndependentWindow: window)
            let width = Int(ceil(filter.contentRect.width * Double(filter.pointPixelScale)))
            let height = Int(ceil(filter.contentRect.height * Double(filter.pointPixelScale)))
            try need(width > 0 && height > 0 && width <= 32768 && height <= 32768 && width * height <= 100_000_000, "sck-window-dimensions-invalid")
            let config = SCStreamConfiguration()
            config.width = width; config.height = height
            config.showsCursor = false
            config.ignoreShadowsSingleWindow = true
            config.captureResolution = .best
            let image = try await SCScreenshotManager.captureImage(contentFilter: filter, configuration: config)
            try need(image.width > 0 && image.height > 0 && image.width * image.height <= 100_000_000, "sck-image-dimensions-invalid")
            let after = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
            let verified = try verifiedWindow(after, pid: pid, id: windowID, title: title)
            try need(verified.frame == window.frame, "sck-window-frame-changed-during-capture")
            guard let destination = CGImageDestinationCreateWithURL(out as CFURL, UTType.png.identifier as CFString, 1, nil) else { throw CaptureError("sck-png-encoder-unavailable") }
            CGImageDestinationAddImage(destination, image, nil)
            try need(CGImageDestinationFinalize(destination), "sck-png-encode-failed")
            emit(["ok": true, "backend": "ScreenCaptureKit/SCScreenshotManager", "pid": pid, "window_id": windowID,
                  "title": title, "width": image.width, "height": image.height, "whole_window": true,
                  "window_activation_used": false, "permission_request_used": false, "pixel_actions_used": false])
        } catch {
            emit(["ok": false, "error": String(describing: error), "permission_request_used": false, "pixel_actions_used": false])
            exit(1)
        }
    }
}
