import React from "react"

export class MultiValueSwitch extends React.Component {
    constructor(props) {
        super(props)
        this.state = {transitioning: false}

        this.fakeRef = null
        this.containerRef = null
        this.buttonRefs = {}
    }

    getChoices() {}

    showOnlyWithChoices() {
        return true
    }

    getLabelForChoice(v) {
        return v
    }

    getSwitchClasses() {
        return "item kars-image-switch always-active"
    }

    getCurrentSelection() {}
    // eslint-disable-next-line no-unused-vars
    changeValue(toValue) {}
    animationDidFinish() {}

    _selectionClass(m) {
        if (m === this.getCurrentSelection()) {
            return "selected"
        }
        return null
    }

    _findSelected() {
        for (let node of this.buttonRefs) {
            if (node.className === "selected") {
                return node
            }
        }
    }

    _transitionClassName() {
        if (this.state.transitioning) {
            return "latched"
        }
        return ""
    }

    transitionAndSet(toValue) {
        if (toValue === this.getCurrentSelection()) {
            return
        }

        const containerL = this.containerRef.getBoundingClientRect().left
        const start = this.buttonRefs[this.getCurrentSelection()]
            .getBoundingClientRect().left - containerL
        const fin = this.buttonRefs[toValue].getBoundingClientRect().left - containerL

        this.changeValue(toValue)

        this.setState({transitioning: true, 
            animInitialPosition: start,
            animTargetPosition: fin
        })
    }

    componentDidUpdate() {
        if (this.fakeRef) {
            this.fakeRef.addEventListener("transitionend", () => {
                this.fakeRef = null
                this.setState({transitioning: false})
                this.animationDidFinish()
            }, {passive: true})

            this.fakeRef.style.marginLeft = this.state.animInitialPosition + "px"
            requestAnimationFrame(() => {
                this.fakeRef.style.marginLeft = this.state.animTargetPosition + "px"
            })
        }
    }

    render() {
        this.buttonRefs = {}

        const choices = this.getChoices()
        if (choices.length < 2 && this.showOnlyWithChoices()) {
            return <div></div>
        }

        return <div className={`${this.getSwitchClasses()} ${this._transitionClassName()}`}
            ref={(r) => this.containerRef = r}>
            {choices.map((v) => {
                return <a key={v} 
                    ref={(r) => this.buttonRefs[v] = r}
                    className={this._selectionClass(v)} 
                    onClick={() => this.transitionAndSet(v)}>
                    {this.getLabelForChoice(v)}
                </a>
            })}

            {this.state.transitioning? <span ref={(r) => this.fakeRef = r} className="fake">
                {this.getLabelForChoice(this.getCurrentSelection())}
            </span> : null}
        </div>
    }
}