import React from "react"
import { connect } from "react-redux"
import { AspectRatio } from "react-aspect-ratio"

import Infra from "./infra"
import { Appearance } from "./appearance"

class _ImageSwitcher extends React.Component {
    constructor(props) {
        super(props)
        this.state = {mode: 1}
    }

    effectiveMode() {
        if (this.props.isGallery) {
            return 3
        } else {
            return this.state.mode
        }
    }

    images() {
        const mode = this.effectiveMode()
        let im = []
        let style = null
        if (this.props.genericBackground) {
            style = {backgroundImage: `url(${this.props.genericBackground})`}
        } 
        if (mode == 1 || mode == 3) {
            im.push(<a key="image-norm" className="kars-card-image-backing" 
                href={this.props.normalImage} alt={Infra.strings["Card image"]} style={style}>
                <AspectRatio ratio="2/1">
                    <img className="kars-card-spread" src={this.props.normalImage} />
                </AspectRatio>
            </a>)
        }
        if (mode == 2 || mode == 3) {
            im.push(<a key="image-idlz" className="kars-card-image-backing" href={this.props.idolizedImage} 
                alt={Infra.strings["Card image"]} style={style}>
                <AspectRatio ratio="2/1">
                    <img className="kars-card-spread" src={this.props.idolizedImage} />
                </AspectRatio>
            </a>)
        }
        return im
    }

    render() {
        const setNorm = () => this.setState({mode: 1})
        const setIdlz = () => this.setState({mode: 2})
        const setBoth = () => this.setState({mode: 3})
        return [
            this.images(),
            <div key="$float" className="kars-card-image-float">
                {this.props.isGallery?
                    <div className="kars-image-switch neutral is-gallery-mode">
                        <a onClick={this.props.exitGalleryMode}>
                            <i className="d-md-none icon ion-md-close" 
                                title={Infra.strings["CISwitch.ExitGalleryMode"]}></i>
                            <span className="d-none d-md-inline">{Infra.strings["CISwitch.ExitGalleryMode"]}</span>
                        </a>
                    </div>
                    :
                    <div className="kars-image-switch neutral">
                        <a onClick={setNorm} className={this.state.mode == 1? "selected" : null}>
                            {Infra.strings["CISwitch.Normal"]}
                        </a>
                        <a onClick={setIdlz} className={this.state.mode == 2? "selected" : null}>
                            {Infra.strings["CISwitch.Idolized"]}
                        </a>
                        <a onClick={setBoth} className={this.state.mode == 3? "selected" : null}>
                            {Infra.strings["CISwitch.Both"]}
                        </a>
                    </div>
                }
            </div>
        ]
    }

    static defrost(Klass, frozen) {
        return <Klass 
            normalImage={frozen.dataset.normalImage} 
            idolizedImage={frozen.dataset.idolizedImage}
            genericBackground={frozen.dataset.genericBg} />
    }
}

class _CardDisplayModeSwitcher extends React.Component {
    isSelected(m) {
        return this.props.appearance.cardDisplayMode === m? "selected" : null
    }

    static modeSwitcherHelp() {
        alert(Infra.strings["CDMSwitch.SwitchHint"])
    }

    render() {
        return <div className="kars-sub-navbar is-right">
            <span className="item">{Infra.strings["CDMSwitch.Title"]}</span>
            <div className="item kars-image-switch always-active">
                <a className={this.isSelected("normal")} 
                    onClick={() => this.props.setDisplay("normal")}>
                    <i className="d-md-none icon ion-ios-list" title={Infra.strings["CDMOption.Normal"]}></i>
                    <span className="d-none d-md-inline">{Infra.strings["CDMOption.Normal"]}</span>
                </a>
                <a className={this.isSelected("esports")} 
                    onClick={() => this.props.setDisplay("esports")}>
                    <i className="d-md-none icon ion-ios-baseball" title={Infra.strings["CDMOption.Esports"]}></i>
                    <span className="d-none d-md-inline">{Infra.strings["CDMOption.Esports"]}</span>
                </a>
                <a className={this.isSelected("gallery")} 
                    onClick={() => this.props.setDisplay("gallery")}>
                    <i className="d-md-none icon ion-ios-images" title={Infra.strings["CDMOption.Gallery"]}></i>
                    <span className="d-none d-md-inline">{Infra.strings["CDMOption.Gallery"]}</span>
                </a>
            </div>
            <a className="has-icon item"
                onClick={CardDisplayModeSwitcher.modeSwitcherHelp}>
                <i className="icon ion-ios-help-circle"></i>
            </a>
        </div>
    }
}

export const ImageSwitcher = connect(
    (state) => {
        return {
            isGallery: (state.appearance.cardDisplayMode === "gallery"),
        }
    },
    (dispatch) => {
        return {
            exitGalleryMode: () => dispatch(
                {type: `${Appearance.actions.setCardDisplayMode}`, payload: "normal"}),
        }
    })(_ImageSwitcher)

export const CardDisplayModeSwitcher = connect(
    (state) => {
        return {
            appearance: state.appearance,
        }
    },
    (dispatch) => {
        return {
            setDisplay: (mode) => dispatch(
                {type: `${Appearance.actions.setCardDisplayMode}`, payload: mode}),
        }
    })(_CardDisplayModeSwitcher)
