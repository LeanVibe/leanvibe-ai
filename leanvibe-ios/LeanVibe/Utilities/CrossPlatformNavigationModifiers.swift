//
//  CrossPlatformNavigationModifiers.swift
//  LeanVibe
//
//  Cross-platform navigation modifiers for iOS/macOS compatibility
//

import SwiftUI

@available(iOS 18.0, macOS 14.0, *)
extension View {
    
    /// Cross-platform navigation bar title display mode
    /// Applies only on iOS, ignored on macOS
    @ViewBuilder
    func crossPlatformNavigationBarTitleDisplayMode(_ displayMode: NavigationBarItem.TitleDisplayMode) -> some View {
        #if os(iOS)
        self.navigationBarTitleDisplayMode(displayMode)
        #else
        self
        #endif
    }
    
    /// Cross-platform toolbar item placement
    /// Uses navigationBarTrailing on iOS, automatic on macOS
    @ViewBuilder
    func crossPlatformToolbarItem<Content: View>(
        @ViewBuilder content: () -> Content
    ) -> some View {
        self.toolbar {
            #if os(iOS)
            ToolbarItem(placement: .navigationBarTrailing) {
                content()
            }
            #else
            ToolbarItem(placement: .automatic) {
                content()
            }
            #endif
        }
    }
    
    /// Cross-platform toolbar item with custom placement
    @ViewBuilder
    func crossPlatformToolbarItem<Content: View>(
        placement: CrossPlatformToolbarPlacement,
        @ViewBuilder content: () -> Content
    ) -> some View {
        self.toolbar {
            ToolbarItem(placement: placement.systemPlacement) {
                content()
            }
        }
    }
}

/// Cross-platform toolbar placement options
@available(iOS 18.0, macOS 14.0, *)
enum CrossPlatformToolbarPlacement {
    case trailing
    case leading
    case automatic
    
    var systemPlacement: ToolbarItemPlacement {
        switch self {
        case .trailing:
            #if os(iOS)
            return .navigationBarTrailing
            #else
            return .automatic
            #endif
        case .leading:
            #if os(iOS)
            return .navigationBarLeading
            #else
            return .automatic
            #endif
        case .automatic:
            return .automatic
        }
    }
}

/// Cross-platform navigation utilities
@available(iOS 18.0, macOS 14.0, *)
struct CrossPlatformNavigation {
    
    /// Standard inline navigation title styling
    @ViewBuilder
    static func inlineTitle<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        content()
            .navigationTitle(title)
            .crossPlatformNavigationBarTitleDisplayMode(.inline)
    }
    
    /// Standard large navigation title styling
    @ViewBuilder
    static func largeTitle<Content: View>(_ title: String, @ViewBuilder content: () -> Content) -> some View {
        content()
            .navigationTitle(title)
            .crossPlatformNavigationBarTitleDisplayMode(.large)
    }
}