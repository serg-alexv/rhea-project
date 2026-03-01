import UIKit
import SwiftUI

/// Root controller for the Rhea keyboard extension.
/// Hosts a SwiftUI `KeyboardView` inside the input view.
///
/// iOS keyboard lifecycle:
///   1. System loads extension process (separate from main app)
///   2. `viewDidLoad` → inflate view hierarchy
///   3. `viewWillAppear` → keyboard about to show
///   4. `textDidChange` → text in host app changed
///
/// The `textDocumentProxy` is our only interface to the host app's
/// text field — we can insert text, delete backward, and read context.
class KeyboardViewController: UIInputViewController {

    private var hostingController: UIHostingController<KeyboardView>?

    override func viewDidLoad() {
        super.viewDidLoad()

        let keyboardView = KeyboardView(
            insertText: { [weak self] text in
                self?.textDocumentProxy.insertText(text)
            },
            deleteBackward: { [weak self] in
                self?.textDocumentProxy.deleteBackward()
            },
            switchKeyboard: { [weak self] in
                self?.advanceToNextInputMode()
            },
            getContext: { [weak self] in
                self?.textDocumentProxy.documentContextBeforeInput ?? ""
            }
        )

        let hosting = UIHostingController(rootView: keyboardView)
        hosting.view.translatesAutoresizingMaskIntoConstraints = false
        hosting.view.backgroundColor = .clear

        addChild(hosting)
        view.addSubview(hosting.view)
        hosting.didMove(toParent: self)

        NSLayoutConstraint.activate([
            hosting.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hosting.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            hosting.view.topAnchor.constraint(equalTo: view.topAnchor),
            hosting.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])

        hostingController = hosting
    }

    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        // Keyboard extensions get 216pt by default; expand for response display
        // Setting a height constraint tells iOS we want more space
    }

    override func textDidChange(_ textInput: UITextInput?) {
        // Called when the text in the host app changes
        // Could update context-aware suggestions here
    }
}
