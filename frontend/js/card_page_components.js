import React from "react"
import { connect } from "react-redux"
import { AspectRatio } from "react-aspect-ratio"

import Infra from "./infra"
import { Appearance } from "./appearance"
import { MultiValueSwitch } from "./ui_lib"
import { requestStoragePermission } from "./storage_permission"

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

    renderClickableCostume() {
        if (this.props.costumeId) {
            return <a href={`/costumes/by_idol/${this.props.memberID}/${this.props.costumeId}`}>
                <img src={this.props.costumeThumb} width="48" alt={Infra.strings.CostumeThumbAlt} />
            </a>
        }
    }

    renderFloat() {
        if (this.props.isGallery) {
            return <>
                {this.renderClickableCostume()}
                <div className="kars-image-switch neutral is-gallery-mode">
                    <a onClick={this.props.exitGalleryMode}>
                        <i className="d-md-none icon ion-md-close"
                            title={Infra.strings.CISwitch.ExitGalleryMode}></i>
                        <span className="d-none d-md-inline">{Infra.strings.CISwitch.ExitGalleryMode}</span>
                    </a>
                </div>
            </>
        } else {
            return <>
                {this.renderClickableCostume()}
                <ImageSwitcherInternal mode={this.state.mode} changeState={(v) => this.setState({mode: v})}/>
            </>
        }
    }

    render() {
        return [
            this.images(),
            <div key="$float" className={`kars-card-image-float ${this.props.isGallery? "is-gallery-mode" : ""}`}>
                {this.renderFloat()}
            </div>
        ]
    }

    static defrost(Klass, frozen) {
        return <Klass
            memberID={frozen.dataset.idol}
            costumeId={frozen.dataset.costumeId}
            costumeThumb={frozen.dataset.costumeThumb}
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
        requestStoragePermission("cdm-switch").then(() => {
            this.props.setDisplay(toValue)
        })
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

async function requestTT(masterVersion, ttID) {
    const xhr = new XMLHttpRequest()
    return new Promise((resolve, reject) => {
        xhr.onreadystatechange = () => {
            if (xhr.readyState !== 4) return
    
            if (xhr.status == 200) {
                const json = JSON.parse(xhr.responseText)
                resolve(json)
            } else {
                reject()
            }
        }
        xhr.open("GET", `/api/v1/${masterVersion}/skill_tree/${ttID}.json`)
        xhr.send()
    })
}
    
export class SkillTreeLoader extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            treeData: null,
            displayType: 0,
            nextComponent: null
        }
    }
    
    expand() {
        this.setState({displayType: 1})
    
        Promise.all([import("./skill-tree/skill_tree"), requestTT(this.props.master, this.props.typeid)])
            .then(([ttMod, ttJson]) => {
                const tree = new ttMod.TTDataAccess(ttJson)
                this.setState({treeData: tree, displayType: 2, nextComponent: ttMod.SkillTreeUI})
            }).catch((exception) => {
                if (!exception) {
                    this.setState({displayType: 3})
                } else {
                    throw exception
                }
            })
    }
    
    render() {
        switch (this.state.displayType) {
        case 0: // Collapsed and no data
            return <div className="kars-tt-placeholder text-center" onClick={() => this.expand()}>
                <i className="icon ion-ios-expand"></i>
                <span className="link-like">{Infra.strings["TTWrapper.ExpandSkillTree"]}</span>
            </div>
        case 1: // Expanded and loading
            return <div className="kars-tt-placeholder text-center">
                <i className="icon ion-ios-hourglass"></i>
                {Infra.strings["TTWrapper.WaitingOnServerForTTData"]}
            </div>
        case 3:
            return <div className="kars-tt-placeholder text-center" onClick={() => this.expand()}>
                <i className="icon ion-ios-hammer"></i>
                {Infra.strings["TTWrapper.FailedToRetrieveTTFromServer"]}
            </div>
        case 2: // Expanded
            const SkillTreeUI = this.state.nextComponent
            return <SkillTreeUI treeData={this.state.treeData} cardId={this.props.cardId} />
        }
    }
    
    static defrost(Klass, frozen) {
        return <Klass
            master={document.body.dataset.master}
            typeid={frozen.dataset.ttId}
            cardId={frozen.dataset.cardId} />
    }
}