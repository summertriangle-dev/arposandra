import React from "react"
import ReactDOM from "react-dom"

function WrapReactModalRenderer(props) {
    return <div className="modal-dialog">
        <div className="modal-content">
            {props.f(props.dismissModal)}
        </div>
    </div>
}

class Modal {
    constructor(f) {
        this.render = f
        this.implicitDismiss = true
        this.didDismiss = null

        this.dom = document.createElement("div")
        this.dom.className = "modal kars-css-modal"
    }

    onDismiss(f) {
        this.didDismiss = f
        return this
    }

    allowsImplicitDismiss(can) {
        this.implicitDismiss = can
        return this
    }

    _mount(dismiss) {
        document.body.appendChild(this.dom)
        ReactDOM.render(<WrapReactModalRenderer f={this.render} dismissModal={dismiss}/>, this.dom)

        setTimeout(() => this.dom.classList.add("shown"))
    }

    _unmount() {
        this.dom.classList.remove("shown")
        setTimeout(() => {
            ReactDOM.unmountComponentAtNode(this.dom)
            document.body.removeChild(this.dom)
            if (this.didDismiss)
                this.didDismiss()    
        }, 200)
    }
}

class _ModalManager {
    constructor() {
        this.backdrop = null
        this.modals = []
    }

    ensureBackdrop() {
        if (!this.backdrop) {
            this.backdrop = document.createElement("div")
            this.backdrop.className = "kars-css-modal-backdrop"
            this.backdrop.addEventListener("click", () => {
                if (this.modals[this.modals.length - 1].implicitDismiss) {
                    this.popModal()
                }
            })

            document.body.appendChild(this.backdrop)
        }
    }

    pushModal(f) {
        this.ensureBackdrop()
        if (!this.backdrop.classList.contains("shown")) {
            setTimeout(() => this.backdrop.classList.add("shown"))
        }

        const modal = new Modal(f)
        modal._mount(() => this.popModal())
        this.modals.push(modal)
    }

    popModal() {
        const modal = this.modals.pop()
        modal._unmount()

        this.backdrop.classList.remove("shown")
    }
}

export const ModalManager = new _ModalManager()
