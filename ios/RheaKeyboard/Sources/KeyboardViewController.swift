import UIKit
import SwiftUI

/// Root controller for the Rhea keyboard extension.
/// Hosts a SwiftUI `KeyboardView` inside the input view.
///
/// The keyboard now has 4 modes: ABC (QWERTY), Quick Actions, Tribunal, Builder.
/// ABC mode provides full letter input; other modes provide AI tools.
/// The `textDocumentProxy` is our only interface to the host app's text field.
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

    override func textDidChange(_ textInput: UITextInput?) {
        // Host app text changed — could drive context-aware features
    }
}
