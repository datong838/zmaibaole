"""Bring Chrome frontmost and focus the window whose active tab hosts the 11-03 daily entry.

Uses AX accessibility channel (AppleScript automation is TCC-denied). Verifies afterwards:
AXFrontmost true, focused window's active web area is /p/home?groupid=1764303851132943.
"""
import json
import sys
import time

import importlib.util as u
spec = u.spec_from_file_location('csd', str(__import__('pathlib').Path(__file__).resolve().with_name('chrome-shell-diagnostic.py')))
m = u.module_from_spec(spec)
spec.loader.exec_module(m)
ins_cls, AXError = m.ChromeShellInspector, m.AXError

EXPECT_HOME = sys.argv[2]
GROUPID = sys.argv[3]

native = None
try:
    native = ins_cls(expected_pid=int(sys.argv[1]))
    cf = native.cf

    def web_url(window):
        def find(elem, depth=0):
            if depth > 8:
                return None
            if native.get(elem, 'AXRole') == 'AXWebArea':
                return native.get(elem, 'AXURL') or ''
            for ch in native.array(elem, 'AXChildren'):
                r = find(ch, depth + 1)
                if r is not None:
                    return r
            return None
        for ch in native.array(window, 'AXChildren'):
            r = find(ch)
            if r:
                return r
        return None

    # 1. frontmost Chrome
    import ctypes as C
    front = native.string('AXFrontmost')
    true_value = C.c_void_p.in_dll(cf, 'kCFBooleanTrue').value
    err = native.ax.AXUIElementSetAttributeValue(native.root, front, true_value)
    cf.CFRelease(front)
    time.sleep(0.8)
    frontmost = native.get(native.root, 'AXFrontmost')

    # 2. locate target window by active web url
    windows = native.array(native.root, 'AXWindows')
    target = None
    for w in windows:
        url = web_url(w) or ''
        main = native.get(w, 'AXMain') is True
        if EXPECT_HOME in url and GROUPID in url and main:
            target = w
            break
    if target is None:
        # fall back: any window whose active web area is the entry URL
        for w in windows:
            url = web_url(w) or ''
            if EXPECT_HOME in url and GROUPID in url:
                target = w
                break
    if target is None:
        raise AXError('entry-window-not-found')

    # 3. make it main/focused
    mainkey = native.string('AXMain')
    err2 = native.ax.AXUIElementSetAttributeValue(target, mainkey, true_value)
    cf.CFRelease(mainkey)
    time.sleep(0.6)
    focused = native.value(native.root, 'AXFocusedWindow')
    focused_url = web_url(focused) if focused else None

    print(json.dumps({
        'ok': True,
        'frontmost': frontmost,
        'set_main_error': err2,
        'focused_window_url': (focused_url or '')[:140],
        'verified': bool(focused_url and EXPECT_HOME in focused_url and GROUPID in focused_url),
    }, ensure_ascii=False, indent=1))
    sys.exit(0)
except (AXError, OSError) as e:
    print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
    sys.exit(2)
finally:
    if native:
        native.close()
