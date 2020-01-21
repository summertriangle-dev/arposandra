import React from "react"
import { connect } from "react-redux"
import { AspectRatio } from "react-aspect-ratio"

import Infra from "./infra"
import { Appearance } from "./appearance"
import { MultiValueSwitch } from "./ui_lib"

class ImageSwitcherInternal extends MultiValueSwitch {
    getChoices() {
        return ["normal", "idolized", "both"]
    }

    getLabelForChoice(v) {
        switch(v) {
        case "normal": return Infra.strings.CISwitch.Option.Normal
        case "idolized": return Infra.strings.CISwitch.Option.Idolized
        case "both": return Infra.strings.CISwitch.Option.Both
        }
    }

    getSwitchClasses() {
        return "kars-image-switch neutral"
    }

    getCurrentSelection() {
        return this.props.mode
    }

    changeValue(toValue) {
        this.props.changeState(toValue)
    }
}

class _ImageSwitcher extends React.Component {
    constructor(props) {
        super(props)
        this.state = {mode: "normal"}
    }

    effectiveMode() {
        if (this.props.isGallery) {
            return "both"
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
        if (mode == "normal" || mode == "both") {
            im.push(<a key="image-norm" className="kars-card-image-backing" 
                href={this.props.normalImage} alt={Infra.strings["Card image"]} style={style}>
                <AspectRatio ratio="2/1">
                    <img className="kars-card-spread" src={this.props.normalImage} />
                </AspectRatio>
            </a>)
        }
        if (mode == "idolized" || mode == "both") {
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
        return [
            this.images(),
            <div key="$float" className="kars-card-image-float">
                {this.props.isGallery?
                    <div className="kars-image-switch neutral is-gallery-mode">
                        <a onClick={this.props.exitGalleryMode}>
                            <i className="d-md-none icon ion-md-close" 
                                title={Infra.strings.CISwitch.ExitGalleryMode}></i>
                            <span className="d-none d-md-inline">{Infra.strings.CISwitch.ExitGalleryMode}</span>
                        </a>
                    </div>
                    :
                    <ImageSwitcherInternal mode={this.state.mode} changeState={(v) => this.setState({mode: v})}/>
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

class _CardDisplayModeSwitcherInternal extends MultiValueSwitch {
    getChoices() {
        return ["normal", "esports", "gallery"]
    }

    getLabelForChoice(v) {
        switch(v) {
        case "normal": 
            return [<i key="$mobile" 
                className="d-md-none icon ion-ios-list" 
                title={Infra.strings.CDM.Option.Normal}></i>,
            <span key="$desktop" 
                className="d-none d-md-inline">{Infra.strings.CDM.Option.Normal}</span>]
        case "esports":
            return [<i key="$mobile" 
                className="d-md-none icon ion-ios-baseball" 
                title={Infra.strings.CDM.Option.Esports}></i>,
            <span key="$desktop" 
                className="d-none d-md-inline">{Infra.strings.CDM.Option.Esports}</span>]
        case "gallery": 
            return [<i key="$mobile" 
                className="d-md-none icon ion-ios-images" 
                title={Infra.strings.CDM.Option.Gallery}></i>,
            <span key="$desktop" 
                className="d-none d-md-inline">{Infra.strings.CDM.Option.Gallery}</span>]
        }
    }

    getCurrentSelection() {
        return this.props.appearance.cardDisplayMode
    }

    changeValue(toValue) {
        this.props.setDisplay(toValue)
    }
}
const CardDisplayModeSwitcherInternal = connect(
    (state) => { return {appearance: state.appearance} },
    (dispatch) => {
        return {
            setDisplay: (mode) => dispatch(
                {type: `${Appearance.actions.setCardDisplayMode}`, payload: mode}),
        }
    })(_CardDisplayModeSwitcherInternal)

export function CardDisplayModeSwitcher() {
    return <div className="kars-sub-navbar is-right">
        <span className="item">{Infra.strings.CDM.Title}</span>
        <CardDisplayModeSwitcherInternal />
        <a className="has-icon item"
            onClick={() => alert(Infra.strings.CDM.SwitchHint)}>
            <i className="icon ion-ios-help-circle"></i>
        </a>
    </div>
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
