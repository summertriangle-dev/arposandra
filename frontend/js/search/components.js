import React from "react"
import Infra from "../infra"
import { isCompletionistSupported } from "./completionist"
import { toHTMLDateInputFormat, isActivationKey } from "./util"

export const CONTROL_TYPE = {
    NUMBER: 1,
    STRING: 2,
    DATETIME: 3,
    STRING_MAX: 4,
    COMPOSITE: 5,
    ENUM: 1000,
    // FIXME: remove
    ENUM_2: 1001,
}

// ----- FORM ---------------------------------------------------------

class PurgatoryRecord {
    constructor(removedName, removedValue, inFavourOf) {
        this.removedName = removedName
        this.removedValue = removedValue
        this.inFavourOf = inFavourOf
    }
}

export class PAQueryEditor extends React.Component {
    constructor(props) {
        super(props)

        const queryTemplateInitial = []
        if (props.query) {
            Object.keys(props.query).forEach((k) => {
                if (k !== "_sort") {
                    queryTemplateInitial.push(k)
                }
            })
        }

        this.state = {
            queryTemplate: queryTemplateInitial,
            queryValues: props.query || {},
            sortBy: props.sortBy || undefined,
            buttonList: this.makeUnusedButtonList(queryTemplateInitial),
            purgatory: null,
            autofocus: null,
        }
    }

    makeUnusedButtonList(template) {
        const buttons = []
        Object.keys(this.props.schema.criteria).forEach((v) => {
            if (!template.includes(v)) {
                buttons.push(v)
            }
        })

        return buttons
    }

    addCriteriaAction(name) {
        console.debug("Panther: add criteria id:", name)
        if (this.state.queryTemplate.indexOf(name) === -1) {
            this.state.queryTemplate.push(name)
        }

        const newState = {
            queryTemplate: this.state.queryTemplate,
            purgatory: null,
            autofocus: name
        }
        const scm = this.props.schema.criteria[name]
        if (scm.behaviour && scm.behaviour.conflicts) {
            for (let i = 0; i < scm.behaviour.conflicts.length; i++) {
                const cfname = scm.behaviour.conflicts[i]
                const where = newState.queryTemplate.indexOf(cfname)

                if (where >= 0) {
                    newState.queryTemplate.splice(where, 1)
                    newState.queryValues = this.state.queryValues

                    const rec = new PurgatoryRecord(cfname, newState.queryValues[cfname], name)
                    delete newState.queryValues[cfname] 
                    newState.purgatory = rec
                }
            }
        }

        newState.buttonList = this.makeUnusedButtonList(newState.queryTemplate)
        this.setState(newState)
    }

    removeCriteriaAction(named) {
        const where = this.state.queryTemplate.indexOf(named)
        const nextState = this.state.queryValues
        if (where >= 0) {
            this.state.queryTemplate.splice(where, 1)
            delete nextState[named]

            this.setState({
                queryTemplate: this.state.queryTemplate, 
                buttonList: this.makeUnusedButtonList(this.state.queryTemplate),
                queryValues: nextState,
                purgatory: null,
                autofocus: null
            })
        }
    }

    setQueryValueAction(key, value) {
        const nextState = this.state.queryValues
        
        if (value === undefined) {
            delete nextState[key]
        } else {
            nextState[key] = value
        }

        this.setState({queryValues: nextState})
    }

    setSortAction(value) {
        this.setState({sortBy: value})
    }

    performSearchAction(e) {
        e.preventDefault()

        this.props.performSearchAction(this.state.queryValues, this.state.sortBy)
    }

    restorePurgatoryAction() {
        const rec = this.state.purgatory
        const nextTemplate = this.state.queryTemplate
        const nextValues = this.state.queryValues
        const toDelete = nextTemplate.indexOf(rec.inFavourOf)

        nextTemplate.splice(toDelete, 1)
        nextTemplate.push(rec.removedName)
        nextValues[rec.removedName] = rec.removedValue
        delete nextValues[rec.inFavourOf]

        this.setState({
            queryTemplate: nextTemplate, 
            queryValues: nextValues, 
            buttonList: this.makeUnusedButtonList(nextTemplate),
            purgatory: null
        })
    }

    render() {
        const actions = {
            addCriteria: this.addCriteriaAction.bind(this),
            removeCriteria: this.removeCriteriaAction.bind(this),
            setQueryValue: this.setQueryValueAction.bind(this),
            setSort: this.setSortAction.bind(this),
            restorePurgatory: this.restorePurgatoryAction.bind(this)
        }

        return <>
            <PASearchButton schema={this.props.schema} performSearchAction={this.performSearchAction.bind(this)} />
            <PAQueryList 
                schema={this.props.schema} 
                editors={this.state.queryTemplate} 
                queryValues={this.state.queryValues}
                sortBy={this.state.sortBy}
                actions={actions}
                autofocus={this.state.autofocus} />
            <PAPurgatoryMessage schema={this.props.schema} record={this.state.purgatory} actions={actions} />
            <PACriteriaList
                schema={this.props.schema} 
                buttonList={this.state.buttonList}
                actions={actions} />
        </>
    }
}

class PASearchButton extends React.Component {
    render() {
        let tf
        if (isCompletionistSupported(this.props.schema.language)) {
            tf = <input type="text" 
                className="form-control search-field" 
                placeholder={Infra.strings.Search.TextBoxHint} />
        } else {
            tf = <input type="text" tabIndex="-1"
                className="form-control search-field" 
                onFocus={(e) => {
                    setTimeout(() => alert(Infra.strings.Search.Error.CompletionistUnsupported))
                    e.target.blur()
                }}
                placeholder={Infra.strings.Search.TextBoxHint} />
        }

        return <div className="form-row mb-4">
            <label className="sr-only" htmlFor="criteria-finder">{Infra.strings.Search.TextBoxSRLabel}</label>
            <div className="search-overlay-grp">
                <i className="overlay icon icon ion-ios-search"></i>
                {tf}
                <input type="submit" 
                    className="btn btn-primary" 
                    value={Infra.strings.Search.ButtonLabel}
                    onClick={this.props.performSearchAction} />
            </div>
        </div>
    }
}

export function PAPurgatoryMessage(props) {
    if (!props.record) {
        return null
    }

    const eh = (e) => {
        e.preventDefault()
        props.actions.restorePurgatory()
    }

    const rname = props.schema.criteria[props.record.removedName].display_name || props.record.removedName
    const ifname = props.schema.criteria[props.record.inFavourOf].display_name || props.record.inFavourOf

    return <div className="mb-2">
        <small>
            <span className="text-warning">{Infra.strings.Search.PurgatoryDescriptionHighlightedPart}</span> 
            {Infra.strings.formatString(Infra.strings.Search.PurgatoryDescription, rname, ifname)}
            {" "} <a href="#" className="font-weight-bold" onClick={eh}>{Infra.strings.Search.RestorePurgatoryLabel}</a>
        </small>
    </div>
}

export function PAFakeSearchButton() {
    return <div className="form-row mb-4">
        <div className="search-overlay-grp">
            <i className="overlay icon icon ion-ios-search"></i>
            <input type="text" 
                className="form-control search-field" 
                placeholder={Infra.strings.Search.TextBoxHint} disabled />
            <input type="submit" 
                className="btn btn-primary" 
                value={Infra.strings.Search.ButtonLabel} disabled />
        </div>
    </div>
}

class PAQueryList extends React.Component {
    renderSingleEditor(k, criteria) {
        let input

        switch(criteria.type) {
        case CONTROL_TYPE.NUMBER:
            input = <PANumericField 
                name={k}
                criteria={criteria}
                value={this.props.queryValues[k]} 
                changeValue={this.props.actions.setQueryValue}
                autofocus={this.props.autofocus == k} />
            break
        case CONTROL_TYPE.DATETIME:
            input = <PADateField 
                name={k}
                criteria={criteria}
                value={this.props.queryValues[k]} 
                changeValue={this.props.actions.setQueryValue}
                autofocus={this.props.autofocus == k} />
            break
        case CONTROL_TYPE.STRING:
        case CONTROL_TYPE.STRING_MAX:
            input = <div className="col-8">
                <input id={`input-for-${k}`}
                    className="form-control" 
                    type="text" 
                    placeholder={criteria.display_name} 
                    maxLength={criteria.max_length}
                    autoFocus={this.props.autofocus == k} />
            </div>
            break
        case CONTROL_TYPE.ENUM:
        case CONTROL_TYPE.ENUM_2:
            input = <PAEnumField name={k} 
                criteria={criteria} 
                value={this.props.queryValues[k]} 
                changeValue={this.props.actions.setQueryValue}
                autofocus={this.props.autofocus == k} />
            break
        default:
            input = <div className="col-8">
                <i className="icon ion-ios-hand"></i>
                Unsupported field type: {criteria.type}
            </div>
        }

        return <div key={k} className="query-editor-row form-group row">
            <div className="col-4 col-form-label">
                <label className="mb-0" htmlFor={`input-for-${k}`}>
                    <a tabIndex={0} 
                        onClick={() => this.props.actions.removeCriteria(k)}
                        onKeyPress={(e) => { if (isActivationKey(e.key)) this.props.actions.removeCriteria(k) }}>
                        <i className="icon icon ion-ios-close-circle text-danger" 
                            title={Infra.strings.Search.RemoveCriteria}></i>
                    </a>
                    {" "}
                    {criteria.display_name || k}
                </label>
            </div>
            {input}
        </div>
    }

    render() {
        if (this.props.editors.length == 0) {
            return null
        }

        return <div className="query-list">
            {this.props.editors.map(
                (k) => this.renderSingleEditor(k, this.props.schema.criteria[k])
            )}

            <div className="query-editor-row form-group row">
                <div className="col-4 col-form-label">
                    <label className="mb-0" htmlFor="input-for-_sort">
                        {Infra.strings.Search.SortBy}
                    </label>
                </div>
                <PASortField 
                    schema={this.props.schema} 
                    value={this.props.sortBy} 
                    changeValue={this.props.actions.setSort} />
            </div>
        </div>
    }
}

class PACriteriaList extends React.Component {
    iconClassForCriteriaName(name) {
        switch (name) {
        case "id":
            return "ion-ios-grid"
        case "ordinal":
            return "ion-ios-list"
        case "member":
            return "ion-ios-bowtie"
        case "max_appeal":
            return "ion-ios-happy"
        case "max_stamina":
            return "ion-ios-heart"
        case "max_technique":
            return "ion-ios-flash"
        case "member_group":
            return "ion-ios-people"
        case "member_subunit":
            return "ion-ios-ribbon"
        case "maximal_stat":
            return "ion-ios-podium"
        case "member_year":
            return "ion-ios-calendar"
        case "skill_major":
            return "ion-ios-color-wand"
        case "skill_minors":
            return "ion-ios-medkit"
        case "rarity":
            return "ion-ios-star"
        case "source":
            return "ion-ios-basket"
        case "role":
            return "ion-ios-move"
        case "attribute":
            return "ion-ios-color-palette"
        default:
            return "ion-ios-cube"
        }
    }

    addCriteriaAction(event) {
        this.props.actions.addCriteria(event.currentTarget.dataset.selectedCriteriaId)
    }

    renderSingleCriteriaButton(key, criteria, act) {
        return <button key={key} data-selected-criteria-id={key} className="btn btn-secondary criteria-button"
            onClick={act}>
            <p className="criteria-icon">
                <i className={`icon icon-lg ${this.iconClassForCriteriaName(key)}`}></i>
            </p>
            <p className="criteria-label">{criteria.display_name || key}</p>
        </button>
    }

    render() {
        if (this.props.buttonList.length == 0) {
            return null
        }

        const act = this.addCriteriaAction.bind(this)
        return <div className="criteria-list pt-3">
            <p className="h6">{Infra.strings.Search.CriteriaBlocksTitle}</p>
            {this.props.buttonList.map(
                (k) => this.renderSingleCriteriaButton(k, this.props.schema.criteria[k], act)
            )}
        </div>
    }
}

// ----- FIELDS -------------------------------------------------------

export class PAEnumField extends React.Component {
    isSplitInput() {
        return (this.props.criteria.behaviour && 
            this.props.criteria.behaviour.compare_type === "bit-set")
    }

    acceptInput(event) {
        const representedValue = parseInt(event.target.value)
        if (this.isSplitInput()) {
            const val = this.props.value || []
            const i = val.indexOf(representedValue)
            if (!event.target.checked) {
                if (i === -1) {
                    val.push(representedValue)
                }
            } else {
                if (i !== -1) {
                    val.splice(i, 1)
                }
            }

            this.props.changeValue(this.props.name, val.length? val : undefined)
        } else {
            if (event.target.value !== ".empty") {
                this.props.changeValue(this.props.name, representedValue)
            } else {
                this.props.changeValue(this.props.name, undefined)
            }
        }
    }

    checkboxValue(forEnumValue) {
        if (this.props.value && this.props.value.indexOf(parseInt(forEnumValue)) !== -1) {
            return false
        }

        return true
    }

    render() {
        let control
        if (this.isSplitInput()) {
            control = <div className="pt-2">
                {this.props.criteria.choices.map((choice, idx) => {
                    // Make implicit focus work.
                    const key = (idx == 0)
                        ? `input-for-${this.props.name}` 
                        : `criteria-${this.props.name}-choice-${choice.value}`

                    return <div key={key} className="form-check form-check-inline">
                        <input id={key} 
                            className="form-check-input" 
                            type="checkbox" 
                            value={choice.value} 
                            autoFocus={idx == 0? this.props.autofocus : undefined}
                            onChange={(e) => this.acceptInput(e)} 
                            checked={this.checkboxValue(choice.value)} />
                        <label htmlFor={key} className="form-check-label">{choice.display_name || choice.name}</label>
                    </div>
                })}
            </div>
        } else {
            control = <select id={`input-for-${this.props.name}`} 
                className="custom-select" 
                value={this.props.value} 
                autoFocus={this.props.autofocus}
                onChange={(e) => this.acceptInput(e)}>
                <option value=".empty">{Infra.strings.Search.EnumPlaceholder}</option>

                {this.props.criteria.choices.map((choice) => 
                    <option key={choice.value} value={choice.value}>{choice.display_name || choice.name}</option>
                )}
            </select>
        }

        return <div className="col-8">
            {control}            
        </div>
    }
}

export class PANumericField extends React.Component {
    constructor(props) {
        super(props)
        this.state = props.value? props.value : {compare_type: "eq", compare_to: null}
    }

    normState() {
        if (this.state.compare_to) {
            const iv = parseInt(this.state.compare_to)
            if (isNaN(iv)) {
                return undefined
            }

            return {compare_type: this.state.compare_type, compare_to: iv}
        } else {
            return undefined
        }
    }

    acceptInput(event) {
        this.setState({compare_to: event.target.value}, () => {
            this.props.changeValue(this.props.name, this.normState())
        })
    }

    acceptCompareType(event) {
        this.setState({compare_type: event.target.value}, () => {
            this.props.changeValue(this.props.name, this.normState())
        })
    }

    render() {
        const isEqualOnly = (this.props.criteria.behaviour && 
            this.props.criteria.behaviour.compare_type === "equal")
        
        if (isEqualOnly) {
            return <div className="col-8">
                <input id={`input-for-${this.props.name}`}
                    className="form-control" 
                    type="text" pattern="[0-9]*" 
                    autoFocus={this.props.autofocus}
                    placeholder={this.props.criteria.display_name} 
                    value={this.state.compare_to || ""}
                    onChange={(event) => this.acceptInput(event)} />
            </div>
        }

        return <>
            {isEqualOnly? null : <div className="col-2">
                <select className="custom-select" 
                    value={this.state.compare_type} 
                    onChange={(event) => this.acceptCompareType(event)}>
                    <option value="gt">{Infra.strings.Search.Operator.GreaterThan}</option>
                    <option value="lt">{Infra.strings.Search.Operator.LessThan}</option>
                    <option value="eq">{Infra.strings.Search.Operator.Equals}</option>
                </select>
            </div>}
            <div className={isEqualOnly? "col-8" : "col-6"}>
                <input id={`input-for-${this.props.name}`}
                    className="form-control" 
                    type="text" pattern="[0-9]*" 
                    autoFocus={this.props.autofocus}
                    placeholder={this.props.criteria.display_name} 
                    value={this.state.compare_to || ""}
                    onChange={(event) => this.acceptInput(event)} />
            </div>    
        </>
    }
}

class PADateField extends PANumericField {
    constructor(props) {
        super(props)
        this.state = props.value? props.value : {compare_type: "gte", compare_to: null}
    }

    normState() {
        if (this.state.compare_to) {
            return this.state
        } else {
            return undefined
        }
    }

    acceptInput(event) {
        this.setState({compare_to: new Date(parseInt(event.target.valueAsNumber))}, () => {
            this.props.changeValue(this.props.name, this.normState())
        })
    }

    render() {
        const d = this.state.compare_to
        let ds = ""
        
        if (d) {
            ds = toHTMLDateInputFormat(d)
        }

        return <>
            <div className="col-2">
                <select className="custom-select" 
                    value={this.state.compare_type} 
                    onChange={(event) => this.acceptCompareType(event)}>
                    <option value="gte">{Infra.strings.Search.Operator.GreaterThanEqual}</option>
                    <option value="lte">{Infra.strings.Search.Operator.LessThanEqual}</option>
                </select>
            </div>
            <div className="col-6">
                <input id={`input-for-${this.props.name}`}
                    className="form-control" 
                    type="date"
                    autoFocus={this.props.autofocus}
                    placeholder={this.props.criteria.display_name} 
                    value={ds}
                    onChange={(event) => this.acceptInput(event)} />
            </div>
        </>
    }
}

export class PASortField extends React.Component {
    acceptInput(event) {
        const representedValue = event.target.value
        if (representedValue !== ".empty") {
            this.props.changeValue(representedValue)
        } else {
            this.props.changeValue(undefined)
        }
    }

    render() {
        let control = <select 
            id="input-for-_sort"
            className="custom-select" 
            value={this.props.value} 
            onChange={(e) => this.acceptInput(e)}>
            <option value=".empty">{Infra.strings.Search.EnumPlaceholder}</option>

            {Object.keys(this.props.schema.criteria).map((choice) => {
                const crit = this.props.schema.criteria[choice]
                if (crit.behaviour && crit.behaviour.sort === false) {
                    return null
                }

                const displayName = crit.display_name || choice

                if (crit.type === 1000 || crit.type === 1001) {
                    if (!crit.behaviour || crit.behaviour.sort !== "numeric") {
                        return <option key={choice} value={"+" + choice}>
                            {displayName}
                        </option>
                    }
                }

                return [
                    <option key={"-" + choice} value={"-" + choice}>
                        {displayName} {Infra.strings.Search.SortDesc}
                    </option>,
                    <option key={"+" + choice} value={"+" + choice}>
                        {displayName} {Infra.strings.Search.SortAsc}
                    </option>
                ]
            })}
        </select>

        return <div className="col-8">
            {control}            
        </div>
    }
}

export class PAPageControl extends React.Component {
    render() {
        const firstPage = Math.max(this.props.page - 3, 1)
        const lastPage = Math.min(this.props.page + 3, this.props.pageCount)
        const items = []

        const go = (p) => {
            if (!this.props.disabled) {
                this.props.moveToPage(p)
            }
        }

        if (firstPage != 1) {
            items.push(
                <li key={1} className={`page-item ${this.props.disabled? "disabled" : ""}`}>
                    <button className="page-link" onClick={() => go(1)}>1</button>
                </li>, <li key="firstEllipsis" className="page-item disabled">
                    <a className="page-link" href="#" tabIndex="-1">...</a>
                </li>
            )
        }

        for (let i = firstPage; i <= lastPage; i++) {
            const active = (i == this.props.page)? "active" : ""
            const disabled = this.props.disabled? "disabled" : ""
            items.push(<li key={i} className={`page-item ${active} ${disabled}`}>
                <button className="page-link" onClick={() => go(i)}>{i}</button>
            </li>)
        }

        if (lastPage != this.props.pageCount) {
            items.push(
                <li key="lastEllipsis" className="page-item disabled">
                    <a className="page-link" href="#" tabIndex="-1">...</a>
                </li>,
                <li key={this.props.pageCount} className={`page-item ${this.props.disabled? "disabled" : ""}`}>
                    <button className="page-link" onClick={() => go(this.props.pageCount)}>
                        {this.props.pageCount}
                    </button>
                </li>
            )
        }

        return <ul className="pagination justify-content-center">
            <li className="page-item disabled">
                <a className="page-link" href="#" tabIndex="-1">{Infra.strings.Search.PaginationTitle}</a>
            </li>
    
            {items}
        </ul>
    }
}