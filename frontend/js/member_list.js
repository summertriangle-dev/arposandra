import Cookies from "js-cookie"
import React from "react"
import Infra from "./infra"
import { requestStoragePermission } from "./storage_permission"
import { MultiValueSwitch } from "./ui_lib"

class MemberListDisplayModeSwitch extends MultiValueSwitch {
    getChoices() {
        return ["normal", "idolized"]
    }

    getLabelForChoice(v) {
        switch(v) {
        case "normal":
            return [<i key="$mobile"
                className="d-md-none icon ion-ios-images"
                title={Infra.strings.CISwitch.Option.Normal}></i>,
            <span key="$desktop"
                className="d-none d-md-inline">{Infra.strings.CISwitch.Option.Normal}</span>]
        case "idolized":
            return [<i key="$mobile"
                className="d-md-none icon ion-ios-bowtie"
                title={Infra.strings.CISwitch.Option.Idolized}></i>,
            <span key="$desktop"
                className="d-none d-md-inline">{Infra.strings.CISwitch.Option.Idolized}</span>]
        }
    }

    getSwitchClasses() {
        return "item kars-image-switch always-active"
    }

    getCurrentSelection() {
        return this.props.mode
    }

    changeValue(toValue) {
        this.props.changeMode(toValue)
    }
}

export class MemberListDisplaySwitcher extends React.Component {
    constructor(props) {
        super(props)
        const mode = MemberListDisplaySwitcher.modeFromCookieValue(Cookies.get("ml_icon_type"))
        this.state = {mode}
    }

    static modeFromCookieValue(cookie) {
        if (cookie === "idolized") {
            return "idolized"
        } else {
            return "normal"
        }
    }

    changeMode(newMode) {
        requestStoragePermission().then((havePermission) => {
            if (havePermission) {
                this.setState({mode: newMode})
                Cookies.set("ml_icon_type", newMode, {expires: 1333337})
                setTimeout(() => window.location.reload(), 300)
            }
        })
    }

    render() {
        return <div className="kars-sub-navbar is-inline is-right">
            <span className="item">Icons</span>
            <MemberListDisplayModeSwitch mode={this.state.mode} changeMode={(m) => this.changeMode(m)} />
        </div>
    }

    static defrost(Klass) {
        return <Klass />
    }
}