import React from "react"
import Infra from "../infra"
import {AspectRatio} from "react-aspect-ratio"

let hackForUnescapingHTML = null
function dmUnescape(s) {
    hackForUnescapingHTML.innerHTML = s
    return hackForUnescapingHTML.value.replace(/<br\/?>/g, "\n")
}

function ADVTalkRenderObj(props) {
    return <div className="kars-list-alternate kars-story-cell">
        <p className="font-weight-bold mb-1">{props.name}</p>
        <p className="my-0 kars-pre-wrap">{props.text}</p>
    </div>
}

function ADVImageRenderObj(props) {
    return <div className="kars-list-alternate">
        <AspectRatio ratio="2/1">
            <img src={`${props.imageUrlBase}/${props.ik}.jpg`} />
        </AspectRatio>
    </div>
}

class ADVTalkCommand {
    constructor(vector) {
        this.name = dmUnescape(vector[0])
        this.text = dmUnescape(vector[1])
        this.renderType = "talk"
    }

    getName() {
        const name = this.name === "[player]"?
            Infra.strings.SST.PlayerName : this.name
        return name
    }

    getText() {
        return this.text
    }
}

class ADVCgCommand {
    constructor(vector) {
        this.cgKey = vector[1]
        if (vector[2] === "load") {
            let subvec = vector[3].split("|")
            this.renderType = "cgPreload"
            this.cgReference = subvec[subvec.length - 1]
        }
        if (vector[2] === "show") {
            this.renderType = "cg"
        }

        this.cgS = vector.join()
    }
}

// You need to list all known keywords here or else they
// will be interpreted as talk commands!
const keywords = {
    "&const": null,
    "goto": null,
    "select": null,
    "wait": null,
    "waitclick": null,
    "waittext": null,
    "waitload": null,
    "suspend": null,
    "resume": null,
    "delay": null,
    "enddelay": null,
    "if": null,
    "else": null,
    "endif": null,
    "sound": null,
    "fade": null,
    "changewindow": null,
    "window	": null,
    "thumbnail": null,
    "clear": null,
    "textmode": null,
    "singletext	": null,
    "textspeed": null,
    "click": null,
    "preload": null,
    "movement": null,
    "letterbox": null,
    "letterimage": null,
    "pillerbox": null,
    "pillerimage": null,
    "message": null,
    "effection": null,
    "lap": null,
    "debugprint": null,
    "ch": null,
    "sp": null,
    "bg": null,
    "cg": ADVCgCommand,
    "em": null,
    "ef": null,
    "ot": null,
    "se": null,
    "all": null,
    "sub-": null,
    "load": null,
    "pos": null,
    "rot": null,
    "scale": null,
    "size": null,
    "color": null,
    "layer": null,
    "plane": null,
    "depth": null,
    "show": null,
    "hide": null,
    "delete": null,
    "move": null,
    "rotation": null,
    "scaling": null,
    "coloring": null,
    "shake": null,
    "stopshake": null,
    "material": null,
    "message": null,
    "mix": null,
    "divide": null,
    "effection": null,
    "viewing": null,
    "fadesetting": null,
    "bgmfade": null,
    "soundstop": null,
    "label": null,
    "window": null,
    "volume": null,
}

class ScriptWalker {
    constructor(base) {
        this.urlBase = base
        this.cgBlacklist = []
        this.cgReferences = {}
        this.alreadyReferenced = []
    }

    walk(stream) {
        let rep = []
        for (let cmd of stream) {
            switch(cmd.renderType) {
            case "talk":
                rep.push(ADVTalkRenderObj({name: cmd.getName(), text: cmd.getText()}))
                break
            case "cgPreload":
                if (this.alreadyReferenced.indexOf(cmd.cgReference) !== -1) {
                    this.cgBlacklist.push(cmd.cgKey)
                    break
                }
                this.cgReferences[cmd.cgKey] = cmd.cgReference
                this.alreadyReferenced.push(cmd.cgReference)
                break
            case "cg":
                if (this.cgBlacklist.indexOf(cmd.cgKey) === -1) {
                    rep.push(ADVImageRenderObj({
                        imageUrlBase: this.urlBase,
                        ik: this.cgReferences[cmd.cgKey]
                    }))
                }
                break
            }
        }
        return rep
    }
}

class ScriptData {
    constructor(theJSON) {
        this.isReady = false
        if (theJSON.rsrc) {
            this.resourceSegment = ScriptData.parseResourceSegment(theJSON.rsrc)
        }
        this.commands = ScriptData.parseDataSegment(theJSON.data)
    }

    static parseDataSegment(text) {
        let commandStream = []
        const lines = text.split(/\n+/)

        if (!hackForUnescapingHTML) {
            hackForUnescapingHTML = document.createElement("textarea")
        }

        for (let cmd of lines) {
            if (!cmd || cmd[0] == "#") {
                continue
            }

            let m = cmd.match(/([^\s]+)/)
            if (!m) {
                continue
            }

            const handler = keywords[m[1]]
            if (handler === undefined) {
                commandStream.push(new ADVTalkCommand(cmd.split(" ")))
                continue
            }

            if (handler === null) {
                continue
            }

            commandStream.push(new handler(cmd.split(" ")))
        }
        return commandStream
    }

    static parseResourceSegment(text) {
        const lines = text.split(/\n+/)
        const manifest = lines[0].match(/([a-z]+)=([0-9]+)/g)

        for (let stmt of manifest) {
            console.log(stmt)
        }
    }

    static async initWithURL(url) {
        const xhr = new XMLHttpRequest()
        return new Promise((resolve, reject) => {
            xhr.onreadystatechange = () => {
                if (xhr.readyState !== 4) return

                if (xhr.status == 200) {
                    const json = JSON.parse(xhr.responseText)
                    resolve(new ScriptData(json.result))
                } else {
                    reject()
                }
            }
            xhr.open("GET", url)
            xhr.send()
        })
    }
}

export class StoryViewer extends React.Component {
    constructor(props) {
        super(props)
        this.state = {scriptData: null}
    }

    componentDidMount() {
        ScriptData.initWithURL(this.props.scriptName).then((s) => {
            this.setState({scriptData: s,
                scriptRender: (new ScriptWalker(this.props.scriptBasename)).walk(s.commands) })
        })
    }

    renderWithScript() {
        return <div>
            <h1 className="h3 ml-3 mb-3">{Infra.strings.SST.Header}</h1>
            <div className="card kars-card-box">
                {this.state.scriptRender}
            </div>
        </div>
    }

    renderStillLoading() {
        return <div>
            <h1 className="h3 ml-3 mb-3">{Infra.strings.SST.Header}</h1>
            <div className="card kars-card-box">
                <div className="card-body">{Infra.strings.SST.LoadingPleaseWait}</div>
            </div>
        </div>
    }

    render() {
        if (this.state.scriptData) {
            return this.renderWithScript()
        } else {
            return this.renderStillLoading()
        }
    }

    static defrost(Klass, frozen) {
        const titleTag = document.querySelector("title")
        titleTag.textContent = `${Infra.strings.SST.Header} - ${titleTag.textContent}`
        const url = new URL(frozen.dataset.signedUrl)
        return <Klass
            scriptBasename={`${url.origin}/advg/${frozen.dataset.name}`}
            scriptName={frozen.dataset.signedUrl}
            scriptRegion={frozen.dataset.scriptRegion} />
    }
}