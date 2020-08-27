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
        this.willDismiss = null

        this.dom = document.createElement("div")
        this.dom.className = "modal kars-css-modal"
    }

    onBeginDismiss(f) {
        this.willDismiss = f
        return this
    }

    onDismiss(f) {
        this.didDismiss = f
        return this
    }

    allowsImplicitDismiss(can) {
        this.implicitDismiss = can
        return this
    }

    _mount(intoElement, dismiss) {
        intoElement.appendChild(this.dom)
        ReactDOM.render(<WrapReactModalRenderer f={this.render} dismissModal={dismiss}/>, this.dom)

        setTimeout(() => this.dom.classList.add("shown"))
    }

    _unmount() {
        this.dom.classList.remove("shown")
        if (this.willDismiss)
            this.willDismiss() 
        setTimeout(() => {
            ReactDOM.unmountComponentAtNode(this.dom)
            this.dom.parentNode.removeChild(this.dom)
            if (this.didDismiss)
                this.didDismiss()    
        }, 200)
    }
}

class _ModalManager {
    constructor() {
        this.backdrop = null
        this.container = null
        this.isBusy = false
        this.dismissBackdropInProgress = null
        this.modals = []
    }

    ensureBackdrop() {
        if (!this.backdrop) {
            this.backdrop = document.createElement("div")
            this.backdrop.className = "kars-css-modal-backdrop"
            this.backdrop.addEventListener("click", () => {
                if (this.isBusy) {
                    return
                }

                if (this.modals[this.modals.length - 1].implicitDismiss) {
                    this.popModal()
                } else {
                    this.shakeTop()
                }
            })

            this.container = document.createElement("div")
            this.container.className = "modal-container"

            document.body.appendChild(this.backdrop)
            document.body.appendChild(this.container)
        }

        if (this.dismissBackdropInProgress) {
            clearTimeout(this.dismissBackdropInProgress)
        }
    }

    shakeTop() {
        this.isBusy = true
        const modal = this.modals[this.modals.length - 1]
        if (!modal) {
            return
        }

        modal.dom.addEventListener("animationend", () => {
            modal.dom.classList.remove("shake")
            this.isBusy = false
        }, {once: true})
        modal.dom.classList.add("shake")
    }

    pushModal(f) {
        this.ensureBackdrop()
        if (!this.backdrop.classList.contains("shown")) {
            setTimeout(() => this.backdrop.classList.add("shown"))
        }

        if (this.modals.length > 0) {
            this.modals[this.modals.length - 1].dom.classList.add("inactive")
        }

        const modal = new Modal(f)
        modal._mount(this.container, () => this.popModal())
        this.modals.push(modal)
        return modal
    }

    popModal() {
        const modal = this.modals.pop()
        modal._unmount()

        if (this.modals.length == 0) {
            this.backdrop.classList.remove("shown")
            this.dismissBackdropInProgress = setTimeout(() => {
                document.body.removeChild(this.backdrop)
                document.body.removeChild(this.container)
                this.backdrop = null
                this.container = null
                this.dismissBackdropInProgress = null
            }, 200)
        } else {
            this.modals[this.modals.length - 1].dom.classList.remove("inactive")
        }
    }
}

export const ModalManager = new _ModalManager()
