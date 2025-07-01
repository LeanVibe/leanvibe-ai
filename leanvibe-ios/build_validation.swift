#!/usr/bin/env swift

import Foundation

// Simple Swift file to test basic compilation
// This will help identify basic syntax and import issues

// Test basic availability
@available(iOS 18.0, macOS 14.0, *)
struct TestStruct {
    let value: String = "test"
}

@available(iOS 18.0, macOS 14.0, *)
class TestClass: ObservableObject {
    @Published var isWorking = true
    
    init() {
        print("Basic Swift compilation test")
    }
}

// Test imports that are commonly used
#if canImport(SwiftUI)
import SwiftUI
print("SwiftUI import: ✅")
#else
print("SwiftUI import: ❌")
#endif

#if canImport(Combine)
import Combine
print("Combine import: ✅") 
#else
print("Combine import: ❌")
#endif

#if canImport(Foundation)
import Foundation
print("Foundation import: ✅")
#else
print("Foundation import: ❌")
#endif

print("Basic compilation test completed")