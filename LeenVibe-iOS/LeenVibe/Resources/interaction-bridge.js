// Bridge for communication between WKWebView and the iOS app

function sendNodeTap(nodeId) {
    window.webkit.messageHandlers.nodeTapped.postMessage(nodeId);
}
