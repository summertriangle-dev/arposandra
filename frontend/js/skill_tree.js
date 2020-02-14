import React from "react"
import Infra from "./infra"
import { TTUserConfiguration, TTDataAccess } from "./tt_internal"
import { AlbumStore } from "./album"

const toRadians = (i) => Math.PI / 180 * i

// https://stackoverflow.com/a/52172400
function hexPoints(cx, cy, r) {
    const step = (360 / 6) | 0
    let points = []
    for (let i = 0; i < 7; i++) {
        const ang = toRadians(step * i - 90)
        points.push(`${Math.round(cx + r * Math.cos(ang))},${Math.round(cy + r * Math.sin(ang))}`)
    }
    return points.join(" ")
}

function starPoints(cx, cy, r1, r2) {
    const step = (360 / 5) | 0
    let points = []
    for (let i = 0; i < 6; i++) {
        const angP = toRadians(step * i - 90)
        const angV = toRadians(step * i - (90 - step / 2))
        points.push(`${Math.round(cx + r1 * Math.cos(angP))},${Math.round(cy + r1 * Math.sin(angP))}`)
        if (i !== 5) {
            points.push(`${Math.round(cx + r2 * Math.cos(angV))},${Math.round(cy + r2 * Math.sin(angV))}`)
        }
    }
    return points.join(" ")
}

function diamondPoints(cx, cy, r) {
    return `${cx},${cy + r} ${cx + r},${cy} ${cx},${cy - r} ${cx - r},${cy}`
}

function starScale(x) {
    switch (x) {
    case 0: return "☆☆☆☆☆"
    case 1: return "★☆☆☆☆"
    case 2: return "★★☆☆☆"
    case 3: return "★★★☆☆"
    case 4: return "★★★★☆"
    case 5: return "★★★★★"
    default: return "★".repeat(x)
    }
}

function classFromNodeType(t) {
    switch(t) {
    case 3: // VOICE
        return "stt-node-voice"
    case 4: // STORY
        return "stt-node-story"
    case 5: // AWAKENING
        return "stt-node-awake" 
    case 6: // SUIT
        return "stt-node-suit"
    case 7: // ACTIVE LEVEL
        return "stt-node-active-level"
    case 8: // HIRAMEKU SLOT
        return "stt-node-hirameku"
    case 9: // PASSIVE LEVEL
        return "stt-node-passive"
    }
}

function labelFromNodeType(t) {
    switch(t) {
    case 3: // VOICE
        return Infra.strings.TTNode.VOICE
    case 4: // STORY
        return Infra.strings.TTNode.STORY
    case 5: // AWAKENING
        return Infra.strings.TTNode.AWAKEN
    case 6: // SUIT
        return Infra.strings.TTNode.COSTUME
    case 7: // ACTIVE LEVEL
        return Infra.strings.TTNode.ACTIVE
    case 8: // HIRAMEKU SLOT
        return Infra.strings.TTNode.INSPIRE
    case 9: // PASSIVE LEVEL
        return Infra.strings.TTNode.PASSIVE
    }
}

function TTGradeLockedParameterCellShaper(props) {
    if (props.requiredGrade > 0) {
        return <polygon points={starPoints(props.cx, props.cy, props.r, props.r * 0.65)} />
    } else {
        return <polygon points={diamondPoints(props.cx, props.cy, props.r)} />
    }
}

const TTNode = React.memo(function TTNode(props) {
    const cellPayload = props.description[2]

    const cx = props.x
    const cy = props.y
    const r = props.squareSize / 2
    // Special cells are drawn a bit bigger
    const sr = Math.ceil(r * 1.25)

    const smallNodeTextOffset = {x: 0, y: 18}
    const smallNodeIconOffset = {x: -10, y: -15}
    const bigNodeTextOffset = {x: 0, y: 22}
    const bigNodeIconOffsetWithText = {x: -27.5, y: -32}
    const bigNodeIconOffsetWithoutText = {x: -27.5, y: -27.5}

    let effectiveBigNodeIconOffset
    if (props.skipTextForBigNodes) {
        effectiveBigNodeIconOffset = bigNodeIconOffsetWithoutText
    } else {
        effectiveBigNodeIconOffset = bigNodeIconOffsetWithText
    }

    let highlight = ""
    if (props.highlighted) {
        highlight = "highlight-path"
    } else if (props.active) {
        highlight = "active-path"
    }

    // FIXME: for all <text>: Remove the tt-s copies once Apple gets their shit together
    // and fixes paint-order in safari.

    switch(cellPayload.type) {
    case 1: // START
        return <g className={`stt-node stt-node-start ${highlight}`}>
            <circle cx={cx} cy={cy} r={Math.ceil(r * 0.5)} />
            <text className="tt-s" x={cx + smallNodeTextOffset.x} y={cy + smallNodeTextOffset.y}>
                {Infra.strings.TTNode.START}</text>
            <text className="tt-t" x={cx + smallNodeTextOffset.x} y={cy + smallNodeTextOffset.y}>
                {Infra.strings.TTNode.START}</text>
        </g>
    case 2: { // PARAMETER
        let cs
        switch(cellPayload.stat) {
        case 2: cs = "p-sta"; break
        case 3: cs = "p-appeal"; break
        case 4: cs = "p-tech"; break
        }
        return <g className={`stt-node stt-node-param ${cs} ${highlight}`}
            onClick={() => props.displayNodeInfo(props.description)}>
            <TTGradeLockedParameterCellShaper requiredGrade={cellPayload.req_grade} cx={cx} cy={cy} r={r} r2={sr} />
            <use href={`/static/images/tt-base.svg#g-stt-node-${cs}`}
                x={cx + smallNodeIconOffset.x} y={cy + smallNodeIconOffset.y}/>
            <text className="tt-s" x={cx + smallNodeTextOffset.x} y={cy + smallNodeTextOffset.y}>
                +{cellPayload.value}</text>
            <text className="tt-t" x={cx + smallNodeTextOffset.x} y={cy + smallNodeTextOffset.y}>
                +{cellPayload.value}</text>
        </g>
    }
    case 3: // VOICE
    case 4: // STORY
    case 5: // AWAKENING
    case 6: // SUIT
    case 7: // ACTIVE LEVEL
    case 8: // HIRAMEKU SLOT
    case 9: // PASSIVE LEVEL
        return <g className={`stt-node stt-node-param ${classFromNodeType(cellPayload.type)} ${highlight}`}
            onClick={() => props.displayNodeInfo(props.description)}>
            <polygon points={hexPoints(cx, cy, sr)} />
            <use href={`/static/images/tt-base.svg#g-${classFromNodeType(cellPayload.type)}`}
                x={cx + effectiveBigNodeIconOffset.x} y={cy + effectiveBigNodeIconOffset.y}/>
            {props.skipTextForBigNodes? null : 
                <text className="tt-s" x={cx + bigNodeTextOffset.x} y={cy + bigNodeTextOffset.y}>
                    {labelFromNodeType(cellPayload.type)}</text>}
            {props.skipTextForBigNodes? null : 
                <text className="tt-t" x={cx + bigNodeTextOffset.x} y={cy + bigNodeTextOffset.y}>
                    {labelFromNodeType(cellPayload.type)}</text>}
        </g>
    }


    return <circle cx={props.x} cy={props.y} r={props.squareSize / 2} />
})

function TTStackConnections(props) {
    const centerIndex = 2
    const contentHeight = props.nodes.length * props.nodeHeight + 
        (props.nodes.length - 1) * props.nodePadding
    const cellHeight = props.nodeHeight + props.nodePadding

    let y = (props.columnHeight - contentHeight) / 2

    let connections = []
    for (let i = 0; i < props.nodes.length; ++i) {
        const v = props.nodes[i]
        if (v === null) continue

        const pY = y + (i * cellHeight) + (props.nodeHeight / 2)
        const pX = Math.abs(i - centerIndex) * (props.columnWidth / 2) + (props.nodeWidth / 2)
        let clz = null
        if (props.isHighlighted(v[0])) {
            clz = "highlight-path"
        } else if (props.isActive(props.depth, i)) {
            clz = "active-path"
        }

        switch(v[1]) {
        case 100:
            connections.push(<line className={clz} key={i}
                x1={pX - props.columnWidth} y1={pY} 
                x2={pX} y2={pY} />)
            break
        case 101: {
            const bX = pX - props.columnWidth / 2
            connections.push(<polyline className={clz} key={i} points={
                `${bX},${y + ((i + 1) * cellHeight)} 
                ${bX},${pY} ${pX},${pY}`
            } />)
            break
        }
        case 102: {
            const bX = pX - props.columnWidth / 2
            connections.push(<polyline className={clz} key={i} points={
                `${bX},${y + ((i - 1) * cellHeight)} 
                ${bX},${pY} ${pX},${pY}`
            } />)
            break
        }
        }
    }

    let lock = null
    if (props.unlockLevel !== undefined) {
        lock = <g>
            <polyline className="stt-level-separator" points={
                `64,0 -24,${props.columnHeight / 2}`} />
            <text className="stt-level-indicator" x="70" y="20">
                {Infra.strings.formatString(Infra.strings["TTWrapper.CardRankShort"], starScale(props.unlockLevel))}
            </text>
        </g>
    }

    return <g transform={`translate(${props.x} 0)`} className="stt-connection">{connections}{lock}</g>
}

function TTStackNodes(props) {
    const centerIndex = 2
    const contentHeight = props.nodes.length * props.nodeHeight + 
        (props.nodes.length - 1) * props.nodePadding
    const cellHeight = props.nodeHeight + props.nodePadding

    let y = (props.columnHeight - contentHeight) / 2

    let graphics = []
    for (let i = 0; i < props.nodes.length; ++i) {
        const v = props.nodes[i]
        if (v === null) continue

        const pY = y + (i * cellHeight)
        const pX = Math.abs(i - centerIndex) * (props.columnWidth / 2)
        graphics.push(<TTNode key={v[0]}
            x={pX + props.nodeWidth / 2} y={pY + props.nodeHeight / 2} 
            squareSize={props.nodeWidth} description={v}
            displayNodeInfo={props.displayNodeInfo}
            highlighted={props.isHighlighted(v[0])}
            active={props.isActive(props.depth, i)} />)
    }

    return <g transform={`translate(${props.x} 0)`}>{graphics}</g>
}

function TTNodeCostInfo(props) {
    return <div>
        <div className="media">
            <figure className="mr-2" style={{fontSize: 0}}>
                <svg width="48" height="48" viewBox="0 0 64 64">
                    <TTNode x={32} y={32} squareSize={48} description={props.node} skipTextForBigNodes={true} />
                </svg>
            </figure>

            <div className="media-text">
                <p className="mb-1 text-uppercase font-weight-bold small text-muted">
                    {Infra.strings["Unlock Requirements:"]}</p>

                <div className="kars-item-list">
                    {props.withIntermediates.materials.map((v, i) => {
                        return <span key={i} className="item">
                            <img src={v.image} width="32" /> x{v.count}
                        </span>
                    })}

                    <span key="$gold" className="item">
                        {props.withIntermediates.gold} G
                    </span>
                </div>
                {props.withIntermediates.grade > 0? 
                    <p className="mb-0 mt-0">
                        {Infra.strings.formatString(Infra.strings["TTWrapper.CardRank"], 
                            starScale(props.withIntermediates.grade))}
                    </p> : null}
                
                <p className="mb-1 small text-muted">
                    {Infra.strings.formatString(Infra.strings["TTWrapper.NIntermediates"], props.intermediateCount - 1)}
                </p>
            </div>
        </div>
    </div>
}

function SkillTree(props) {
    const nodeSize = 48
    const nodePadding = 30
    const columnWidth = (nodeSize + nodePadding) + 32
    const imageXPadding = 100
    const imageHeight = 400
    const imageWidth = (columnWidth * props.treeData.tree.length) + (2 * imageXPadding)

    return <div className="kars-tt-window">
        <svg width={imageWidth} height={imageHeight} 
            viewBox={`0 0 ${imageWidth} ${imageHeight}`}>
            <defs>
                <linearGradient id="stt-awaken-node-fill"
                    x1="0" x2="0" y1="0" y2="1">
                    <stop className="s1" offset="0%"/>
                    <stop className="s2" offset="100%"/>
                </linearGradient>
            </defs>
            {props.treeData.tree.map((v, i) =>
                <TTStackConnections 
                    depth={i}
                    nodeWidth={nodeSize} nodeHeight={nodeSize} nodePadding={nodePadding} 
                    columnHeight={imageHeight} x={imageXPadding + (i * columnWidth)} 
                    columnWidth={columnWidth} 
                    key={i} nodes={v}
                    isHighlighted={props.isHighlighted}
                    isActive={props.isActive} 
                    unlockLevel={props.treeData.lockGradeForLevel(i)}/>
            )}
            {props.treeData.tree.map((v, i) =>
                <TTStackNodes 
                    depth={i}
                    nodeWidth={nodeSize} nodeHeight={nodeSize} nodePadding={nodePadding} 
                    columnHeight={imageHeight} x={imageXPadding + (i * columnWidth)} 
                    columnWidth={columnWidth} 
                    key={i} nodes={v}
                    displayNodeInfo={props.focusNode}
                    isHighlighted={props.isHighlighted}
                    isActive={props.isActive} /> 
            )}
        </svg>
    </div>
}

class TTMiniToolbar extends React.Component {
    constructor(props) {
        super(props)
        this.state = {confirming: false}
    }

    commitReset() {
        this.props.resetAll()
        this.setState({confirming: false})
    }

    render() {
        let costInfo = null
        if (this.props.path) {
            const cumulativeCost = this.props.path? this.props.dataAccess.sumCostForPath(this.props.path) : null
            const onlyTargetCost = this.props.path? this.props.dataAccess.sumCostForPath([this.props.node[0]]) : null
            costInfo = <TTNodeCostInfo node={this.props.node} cost={onlyTargetCost} 
                withIntermediates={cumulativeCost} intermediateCount={this.props.path.length} />
        }

        let content
        if (this.state.confirming) {
            content = <p className="m-0 small">
                <span>
                    {Infra.strings["Really?"]}
                </span>
                {" \u2022 "}
                <a onClick={() => this.commitReset()} className="text-danger">
                    {Infra.strings["Reset"]}
                </a>
                {" - "}
                <a onClick={() => this.setState({confirming: false})} className="text-primary">
                    {Infra.strings["Cancel"]}
                </a>
            </p>
        } else {
            content = <p className="m-0 small">
                {Infra.strings["TTWrapper.UnlockHint"]}
                {" \u2022 "}
                <a onClick={() => this.setState({confirming: true})} className="text-danger">
                    {Infra.strings["Reset All Nodes..."]}
                </a>
                {this.props.path? <span>Debug: tail node ID: {this.props.node[0]} Highlight set: {this.props.path.toString()}</span> : null}
            </p>
        }
        return <div className="kars-tt-thing">
            {costInfo}
            {content}
        </div>
    }
}

export default class WrapSkillTree extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            treeData: null,
            displayType: 0,
            focusNodeInfo: null,
            userConfig: null,
            highlightPath: null,
        }
    }

    checkHighlight(nId) {
        if (this.state.highlightPath) {
            return (TTDataAccess.fastFind(this.state.highlightPath, nId) !== undefined)
        }
        return false
    }

    checkActive(depth, vert) {
        return this.state.userConfig.isNodeActive(depth, vert)
    }

    proposedLB() {
        let max = 0
        for (let i = 0; i < this.state.highlightPath.length; ++i) {
            const p = this.state.treeData.getNodeByID(this.state.highlightPath[i])
            if (p.req_grade > max) {
                max = p.req_grade
            }
        }
        return max
    }

    nodeClicked(node) {
        if (this.state.focusNodeInfo && node[0] === this.state.focusNodeInfo[0]) {
            // naughty but we're going to dispose of it momentarily...
            this.state.userConfig.activateSet(this.state.highlightPath)
            this.setState({
                focusNodeInfo: null,
                highlightPath: null
            })

            const limitBreak = this.proposedLB()
            const influence = this.state.userConfig.calculateStatContributionOfActiveNodes()
            Infra.store.dispatch({
                type: `${AlbumStore.actions.setCardTTInfluence}`, 
                cid: this.props.cardId,
                influence
            })

            const currentLevels = Infra.store.getState().album.cardLevel[this.props.cardId]
            if (!currentLevels || limitBreak > currentLevels.limitBreak) {
                Infra.store.dispatch({
                    type: `${AlbumStore.actions.setCardLimitBreak}`, 
                    cid: this.props.cardId,
                    limitBreak
                })
            }
        } else {
            if (this.state.userConfig.isNodeActiveByID(node[0])) {
                this.setState({focusNodeInfo: null, highlightPath: null})
                return
            }

            this.setState({
                focusNodeInfo: node,
                highlightPath: this.state.userConfig.pathFromAnyHead(node[0])
            })
        }
    }

    resetAndReload() {
        this.state.userConfig.resetState()
        this.setState({treeData: this.state.treeData, userConfig: this.state.userConfig})
    }

    expand() {
        this.setState({displayType: 1})
        TTDataAccess.requestTT(this.props.master, this.props.typeid).then((tree) => {
            const progress = new TTUserConfiguration(tree)
            this.setState({treeData: tree, displayType: 2, userConfig: progress})
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
            return <div>
                <SkillTree treeData={this.state.treeData} 
                    focusNode={(n) => this.nodeClicked(n)}
                    isHighlighted={(nid) => this.checkHighlight(nid)}
                    isActive={(depth, vert) => this.checkActive(depth, vert)} />
                <TTMiniToolbar resetAll={() => this.resetAndReload()}
                    node={this.state.focusNodeInfo}
                    path={this.state.highlightPath}
                    dataAccess={this.state.treeData} />
            </div>
        }
    }

    static defrost(Klass, frozen) {
        return <Klass 
            master={document.body.dataset.master} 
            typeid={frozen.dataset.ttId}
            cardId={frozen.dataset.cardId} />
    }
} 