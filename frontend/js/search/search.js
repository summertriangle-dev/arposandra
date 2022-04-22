import React from "react"
import ReactDOM from "react-dom"
import Infra from "../infra"
import { ModalManager } from "../modals"
import { PAFakeSearchButton, PAPageControl, PAQueryEditor, CONTROL_TYPE } from "./components"
import { serializeQuery, deserializeQuery, isActivationKey, /* simulatedNetworkDelay */ } from "./util"
import { PACardSearchDomainExpert, PAAccessorySearchDomainExpert } from "./domain"

const PASearchProgressState = {
    LoadingSchema: 0,
    EditingQuery: 1,
    Searching: 2,
    LoadingResults: 3,
    ContinueSearch: 4,
    ErrorLoadingCards: 5,
    ErrorLoadingSchema: 6,
}

const RESULTS_PER_PAGE = 12

class PurgatoryRecord {
    constructor(removedName, removedValue, inFavourOf) {
        this.removedName = removedName
        this.removedValue = removedValue
        this.inFavourOf = inFavourOf
    }
}

class PAQueryManager {
    constructor(schema, dictionary, hooks) {
        this.schema = schema
        this.dictionary = dictionary
        this.queryValues = {}
        this.template = []
        this.textBoxControlled = []
        this.sort = null
        this.purgatory = null
        this.savedTextQuery = null
        this.expert = hooks
    }

    _firstCriteriaConflict(withAny, criteriaName) {
        const scm = this.schema.criteria[criteriaName]
        if (scm.behaviour && scm.behaviour.conflicts) {
            for (let i = 0; i < scm.behaviour.conflicts.length; i++) {
                const cfname = scm.behaviour.conflicts[i]
                const where = withAny.indexOf(cfname)
                if (where >= 0) {
                    return cfname
                }
            }
        }

        return null
    }

    setFromURLParameters(queryString) {
        const params = deserializeQuery(this.schema, queryString)
        this.sort = params._sort
        delete params["_sort"]
        delete params["_auto"]
        this.queryValues = params
        this.template = Object.keys(params).slice(0)
    }

    addCriteria(name) {
        console.debug("Panther: add criteria id:", name)
        const nextTemplate = this.template.slice()
        if (nextTemplate.indexOf(name) === -1) {
            nextTemplate.push(name)
        }

        const conflictKey = this._firstCriteriaConflict(nextTemplate, name)
        if (conflictKey !== null) {
            const where = nextTemplate.indexOf(conflictKey)
            nextTemplate.splice(where, 1)
            const nextValues = this.queryValues

            const rec = new PurgatoryRecord(conflictKey, nextValues[conflictKey], name)
            delete nextValues[conflictKey] 

            this.purgatory = rec
            this.queryValues = nextValues
        }

        this.template = nextTemplate
        this.expert.didAddCriteria(this, name)
    }

    removeCriteria(named) {
        const where = this.template.indexOf(named)
        if (where >= 0) {
            this.template.splice(where, 1)
            delete this.queryValues[named]
            this.purgatory = null
        }
    }

    setQueryValue(key, value) {
        if (value === undefined) {
            delete this.queryValues[key]
        } else {
            this.queryValues[key] = value
        }

        let idx
        if ((idx = this.textBoxControlled.indexOf(key)) !== -1) {
            this.textBoxControlled.splice(idx, 1)
        }

        this.expert.didChangeCriteria(this, key)
    }

    _parseTextQuery(str) {
        const quotedWords = []
        const kv = {}

        const splitQuotes = str.split(/"/)
        splitQuotes.forEach((v, i) => {
            if (i % 2 != 0) {
                quotedWords.push(v)
                return
            }

            const words = v.split(/[\s]+/).map((w) => w.trim()).filter((w) => w !== "")
            words.forEach((v) => {
                // 1. direct matched keywords go directly into query
                const ent = this.dictionary[v.toLowerCase()]
                if (ent) {
                    kv[ent.target] = this._textQueryApplyKeyword(ent.target, ent.value, kv[ent.target])
                    return
                } 

                // 2. ask expert if it can understand the word
                const dynamic = this.expert.dynamicKeywordToQueryValues(v)
                if (dynamic) {
                    Object.keys(dynamic).forEach((targ) => {
                        kv[targ] = this._textQueryApplyKeyword(targ, dynamic[targ], kv[targ])
                    })
                } else {
                    // 3. if not, put it into the FTS field
                    quotedWords.push(v)
                }
            })
        })

        const quotedTarget = this.expert.criteriaTargetForQuotedWords()
        if (quotedTarget && quotedWords.length > 0) {
            kv[quotedTarget] = quotedWords.join(" ")
        }

        return kv
    }

    _textQueryApplyKeyword(forCriteria, kwValue, toAggregatedValue) {
        const crStruct = this.schema.criteria[forCriteria]

        // Merge value for checkbox fields
        if ((crStruct.type === CONTROL_TYPE.ENUM || crStruct.type === CONTROL_TYPE.ENUM_2)
            && crStruct.behaviour?.compare_type === "bit-set") {
            const aggregate = toAggregatedValue || crStruct.choices.map(v => v.value)
            const idx = aggregate.indexOf(kwValue)
            if (idx > -1) {
                aggregate.splice(idx, 1)
            }
            return aggregate
        }

        return kwValue
    }

    setTypedQuery(queryString) {
        this.savedTextQuery = queryString
        const map = this._parseTextQuery(queryString)
        Object.keys(map).forEach((key) => {
            if (this.template.indexOf(key) === -1) {
                this.template.push(key)
            }
        })

        this.textBoxControlled.forEach((key) => {
            if (map[key] === undefined) {
                let idx
                if ((idx = this.template.indexOf(key)) !== -1) {
                    this.template.splice(idx, 1)
                }
                
                delete this.queryValues[key]
            }
        })

        this.textBoxControlled = Object.keys(map)
        // console.debug("Text box controlled crits are now:", this.textBoxControlled)
        // console.debug("Template is now:", this.template)
        Object.assign(this.queryValues, map)
    }

    setSort(value) {
        this.sort = value
    }

    restorePurgatory() {
        const rec = this.purgatory
        if (!rec) {
            return
        }

        const toDelete = this.template.indexOf(rec.inFavourOf)
        this.template.splice(toDelete, 1)
        delete this.queryValues[rec.inFavourOf]

        if (rec.removedName) {
            this.template.push(rec.removedName)
            this.queryValues[rec.removedName] = rec.removedValue
        }

        this.purgatory = null
    }

    hasAnyFilterValues() {
        let ret = false
        const keys = Object.keys(this.queryValues)
        for (let i = 0; i < keys.length; ++i) {
            if (this.queryValues[keys[i]] !== undefined) {
                ret = true
            }
        }

        return ret
    }

    setFromPreset(preset, strategy) {
        if (strategy === "replace") {
            this.template = preset.template.slice(0)
            this.queryValues = {}
            this.purgatory = null
        } else {
            const newTemplate = preset.template.slice(0)
            const newVals = Object.assign({}, this.queryValues)
            this.template.forEach((v) => {
                if (this.queryValues[v] && !preset.template.includes(v)) {
                    const hasConflict = this._firstCriteriaConflict(newTemplate, v)
                    if (hasConflict) {
                        delete newVals[hasConflict]
                    } else {
                        newTemplate.push(v)
                    }
                }
            })

            this.template = newTemplate
            this.queryValues = newVals
            this.purgatory = null
        }
    }
}

class PASearchContext {
    constructor(apiType) {
        this.schema = null
        this.dictionary = null

        this.actionSet = {
            addCriteria: (name) => { this.queryManager.addCriteria(name); this.render() },
            removeCriteria: (name) => { this.queryManager.removeCriteria(name); this.render() },
            setQueryValue: (key, value) => { this.queryManager.setQueryValue(key, value); this.render() },
            setTypedQuery: (str) => { this.queryManager.setTypedQuery(str); this.render() },
            setSort: (column) => { this.queryManager.setSort(column); this.render() },
            restorePurgatory: () => { this.queryManager.restorePurgatory(); this.render() },
            applyPreset: (preset) => { this.applyPresetAction(preset) },
            performSearch: () => this.performSearchAction(),
        }

        this.currentResults = []
        this.currentPage = 0

        this.flightState = PASearchProgressState.LoadingSchema
        this.isFirstLoad = true

        this.recoveryInfo = null
        this.inlineErrorMessage = null

        switch (apiType) {
        case "cards": this.api = new PACardSearchDomainExpert(); break
        case "accessories": this.api = new PAAccessorySearchDomainExpert(); break
        }

        this.queryManager = new PAQueryManager(this.schema, this.dictionary, this.api)
    }

    askUserForPresetMergeBehaviour() {
        return new Promise((resolve) => {
            if (!this.queryManager.hasAnyFilterValues()) {
                resolve("replace")
                return
            }

            ModalManager.pushModal((dismiss) => {
                const dismissReturn = (v) => {
                    resolve(v)
                    dismiss()
                }
    
                return <section className="modal-body">
                    <p>{Infra.strings.Search.ReplacePresetPromptText}</p>
                    <div className="form-row kars-fieldset-naturalorder">
                        <button className="item btn btn-primary" autoFocus={true}
                            onClick={() => dismissReturn("merge")}>
                            {Infra.strings.Search.ReplacePresetPromptMerge}</button>
                        <button className="item btn btn-secondary"
                            onClick={() => dismissReturn("replace")}>
                            {Infra.strings.Search.ReplacePresetPromptReplace}</button>
                        <button className="item btn btn-tertiary"
                            onClick={() => dismissReturn("cancel")}>
                            {Infra.strings.Search.ReplacePresetPromptCancel}</button>
                    </div>
                </section>
            }).onDismiss(() => resolve("cancel"))
        })
    }

    applyPresetAction(preset) {
        if (!preset) return

        this.askUserForPresetMergeBehaviour().then((behaviour) => {
            if (behaviour === "cancel") {
                return
            }

            this.queryManager.setFromPreset(preset, behaviour)
            this.render()
        })
    }

    transitionToState(state) {
        console.debug("Panther: moving to UI state", state)
        this.flightState = state

        if (this.flightState == PASearchProgressState.LoadingResults
            || this.flightState == PASearchProgressState.Searching) {
            // Provide some indication that the current display is stale.
            const host = document.getElementById("results-host")
            host.style.opacity = 0.5

            const pager = document.getElementById("pager-host")
            ReactDOM.render(<PAPageControl 
                disabled={true}
                page={this.currentPage + 1} 
                pageCount={this.pageCount()} 
                moveToPage={this.moveToPageAction.bind(this)} />, pager)
        }

        this.render()
    }

    render() {
        const placement = document.getElementById("query-editor-host")
        let widget = null

        switch (this.flightState) {
        case PASearchProgressState.LoadingSchema:
            widget = <>
                <PAFakeSearchButton />
                <div className="text-center">
                    <span className="h6">{Infra.strings.Search.StateMessage.LoadingSchema}</span>
                </div>
            </>
            break
        case PASearchProgressState.EditingQuery:
        case PASearchProgressState.ErrorZeroResults:
            widget = <PAQueryEditor 
                schema={this.schema} 
                savedText={this.queryManager.savedTextQuery}
                queryValues={this.queryManager.queryValues}
                template={this.queryManager.template}
                sortBy={this.queryManager.sort}
                purgatory={this.queryManager.purgatory}
                actionSet={this.actionSet}
                errorMessage={this.inlineErrorMessage}
                expert={this.api} />
            break
        case PASearchProgressState.ContinueSearch:
            widget = <div className="text-center">
                <i className="icon ion-ios-search"></i>
                <a className="h6" onClick={(e) => { 
                    e.preventDefault()
                    this.transitionToState(PASearchProgressState.EditingQuery) 
                }} href="#">{Infra.strings.Search.StateMessage.Continue}</a>
            </div>
            break
        case PASearchProgressState.Searching:
            widget = <PAGenericMessage message={Infra.strings.Search.StateMessage.Searching} />
            break
        case PASearchProgressState.LoadingResults:
            widget = <PAGenericMessage message={Infra.strings.Search.StateMessage.LoadingCards} />
            break
        case PASearchProgressState.ErrorLoadingCards:
            widget = <PACardLoadErrorMessage 
                action={this.performErrorRecovery.bind(this)}
                editQueryAction={() => this.transitionToState(PASearchProgressState.EditingQuery)} />
            break
        case PASearchProgressState.ErrorLoadingSchema:
            widget = <PASchemaLoadErrorMessage 
                action={this.performErrorRecovery.bind(this)} />
            break
        }

        ReactDOM.render(widget, placement)
    }

    displayErrorModal(message) {
        ModalManager.pushModal((dismiss) => {
            return <section className="modal-body">
                <p>{message}</p>
                <div className="form-row kars-fieldset-naturalorder">
                    <button className="item btn btn-primary" 
                        autoFocus={true}
                        onClick={dismiss}>{Infra.strings.Search.DismissErrorModal}</button>
                </div>
            </section>
        })
    }

    performSearchAction() {
        if (Object.keys(this.queryManager.queryValues).length == 0) {
            return this.displayErrorModal(Infra.strings.Search.Error.NoCriteriaValues)
        }

        const nq = {}
        Object.assign(nq, this.queryManager.queryValues)
        if (this.queryManager.sort) {
            nq["_sort"] = this.queryManager.sort
        }

        const hash = serializeQuery(this.schema, nq)
        // try not to clear the autosearch query
        if (!this.isFirstLoad) {
            history.pushState(null, document.title, this.currentURLBase() + "?" + hash)
        }
        this.inlineErrorMessage = null

        this.transitionToState(PASearchProgressState.Searching)
        this.api.sendSearchRequest(nq).catch((error) => {
            this.displayResultList([], 0, true, error.error)
            this.transitionToState(PASearchProgressState.EditingQuery)
        }).then((results) => {
            if (!results) {
                return
            }

            this.displayResultList(results.result || [], 0)
        })
    }

    historyBackAction(event) {
        if (event.state) {
            this.displayResultList(event.state.results, event.state.page)
        }
    }

    moveToPageAction(pNum) {
        window.scrollTo(0, 0)
        // uhh....
        history.pushState(
            {results: this.currentResults, page: pNum - 1}, 
            `${document.title} (${pNum}/${this.pageCount()})`,
            window.location.href)

        this.displayResultList(this.currentResults, pNum - 1, false)
    }

    currentURLBase() {
        return `${window.location.protocol}//${window.location.host}${window.location.pathname}`
    }

    pageCount() {
        return Math.ceil(this.currentResults.length / RESULTS_PER_PAGE)
    }

    async displayResultList(results, page, editHistory=true, error=null) {
        this.currentResults = results
        this.currentPage = page || 0

        const header = document.getElementById("info-host")
        if (this.currentResults.length > 0) {
            this.transitionToState(PASearchProgressState.LoadingResults)

            if (editHistory) {
                history.replaceState(
                    {results: this.currentResults, page: this.currentPage}, 
                    document.title, window.location.href)
            }

            const idl = this.currentResults.slice(this.currentPage * RESULTS_PER_PAGE, 
                (this.currentPage + 1) * RESULTS_PER_PAGE)
            
            // ----- async break point -----
            let doc
            try {
                doc = await this.api.sendAjaxRequest(idl)
            } catch (rejectReason) {
                ReactDOM.render(null, header)
                ReactDOM.render(null, document.getElementById("results-host"))
                ReactDOM.render(null, document.getElementById("pager-host"))

                this.recoveryInfo = {results, page}
                this.transitionToState(PASearchProgressState.ErrorLoadingCards)
                return
            }

            this.transitionToState(PASearchProgressState.ContinueSearch)
            const host = document.getElementById("results-host")
            const incoming = doc.getElementById("results-host")
            incoming.parentNode.removeChild(incoming)
            host.parentNode.insertBefore(incoming, host)
            host.parentNode.removeChild(host)

            ReactDOM.render(
                <p>
                    {Infra.strings.formatString(
                        Infra.strings.Search.NumResultsLabel, 
                        Infra.strings.Search.NumResultsFormat(results.length))}
                </p>, header
            )

            const pager = document.getElementById("pager-host")
            ReactDOM.render(
                <PAPageControl page={this.currentPage + 1} 
                    pageCount={this.pageCount()} 
                    moveToPage={this.moveToPageAction.bind(this)} />,
                pager)
        } else {
            if (!error) {
                this.inlineErrorMessage = Infra.strings.Search.Error.NoResults
                this.transitionToState(PASearchProgressState.EditingQuery)
            } else {
                this.inlineErrorMessage = Infra.strings.formatString(
                    Infra.strings.Search.Error.ExecuteFailed, error)
                // No transition - it's handled in performSearchAction
            }

            const host = document.getElementById("results-host")
            host.className = ""
            host.style.opacity = 1.0

            ReactDOM.render(null, header)
            ReactDOM.render(null, host)
            ReactDOM.render(null, document.getElementById("pager-host"))
        }
    }

    async sendSchemaRequest(toUrl) {
        // await simulatedNetworkDelay(500)
        // return Promise.reject({error: "error", url: toUrl})

        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                console.debug("Panther: did finish loading schema with result: " + xhr.status)
                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    reject({error: `http(${xhr.status})`, url: toUrl})
                }
            }
            xhr.open("GET", toUrl)
            xhr.send()
        })
    }

    async reloadSchema(overlayURLs, dictionaryURLs) {
        this.transitionToState(PASearchProgressState.LoadingSchema)

        const schemaPs = Promise.all(overlayURLs.map((x) => this.sendSchemaRequest(x)))
        let schemas = null
        try {
            schemas = await schemaPs
        } catch (rejection) {
            this.recoveryInfo = {overlayURLs, dictionaryURLs}
            this.transitionToState(PASearchProgressState.ErrorLoadingSchema)
            return
        }

        if (schemas !== null) {
            this.schema = schemas[0]
            if (!this.schema.presets) {
                this.schema.presets = []
            }

            for (let i = 1; i < schemas.length; ++i) {
                const overlay = schemas[i].criteria
                for (let j in overlay) {
                    if (Object.hasOwnProperty.call(overlay, j)) {
                        Object.assign(this.schema.criteria[j], overlay[j])
                    }
                }
                if (schemas[i].presets) {
                    this.schema.presets.push(...schemas[i].presets)
                }
            }
            this.queryManager.schema = this.schema
        }

        const dictionaryPs = Promise.all(dictionaryURLs.map((x) => this.sendSchemaRequest(x)))
        let dicts
        try {
            dicts = await dictionaryPs
        } catch (rejection) {
            this.recoveryInfo = {overlayURLs, dictionaryURLs}
            this.transitionToState(PASearchProgressState.ErrorLoadingSchema)
        }

        const dictionary = {}
        Object.assign(dictionary, ...dicts.map(v => v.dictionary))
        this.dictionary = dictionary
        this.queryManager.dictionary = dictionary
    }

    performFirstLoadStateRestoration() {
        let auto = false
        let queryFromURL = null

        if (window.location.search) {
            queryFromURL = window.location.search.substring(1)
        } else if (window.location.hash) {
            queryFromURL = window.location.hash.substring(1)
            history.replaceState(null, document.title, this.currentURLBase() + "?" + queryFromURL)
        }

        if (queryFromURL) {
            this.queryManager.setFromURLParameters(queryFromURL)
            if (this.queryManager.template.length > 0) {
                auto = true
            }
        } else {
            this.queryManager.setFromPreset(this.schema.presets?.[0], "replace")
        }

        if (history.state && Array.isArray(history.state.results)) {
            this.displayResultList(history.state.results, history.state.page || 0)
        } else if (auto) {
            this.performSearchAction()
        } else {
            this.transitionToState(PASearchProgressState.EditingQuery)
        }

        window.addEventListener("popstate", this.historyBackAction.bind(this))
        this.isFirstLoad = false
    }

    performErrorRecovery() {
        if (this.flightState === PASearchProgressState.ErrorLoadingCards) {
            this.displayResultList(this.recoveryInfo.results, this.recoveryInfo.page, false)
        } else {
            this.reloadSchema(this.recoveryInfo.overlayURLs, this.recoveryInfo.dictionaryURLs).then(() => {
                if (!this.schema || !this.dictionary) {
                    return 
                }

                if (this.isFirstLoad) {
                    this.performFirstLoadStateRestoration()
                } else {
                    this.transitionToState(PASearchProgressState.EditingQuery)
                }
            })
        }

        this.recoveryInfo = null
    }
}

function PAGenericMessage(props) {
    return <div className="text-center">
        <i className="icon ion-ios-search"></i>
        <span className="h6">{props.message}</span>
    </div>
}

function PASchemaLoadErrorMessage(props) {
    const eh = (e) => {
        e.preventDefault()
        if (e.key === undefined || isActivationKey(e.key)) {
            props.action()
        }
    }

    return <div className="text-center">
        <p className="h6 mb-0">
            <i className="icon ion-ios-warning text-danger"></i>
            {Infra.strings.formatString(Infra.strings.Search.Error.SchemaLoad,
                <a href="#" onClick={(e) => eh(e, props.action)} onKeyPress={(e) => eh(e, props.action)}>
                    {Infra.strings.Search.Error.TryAgain}
                </a>
            )}
        </p>
    </div>
}

function PACardLoadErrorMessage(props) {
    const eh = (e, a) => {
        e.preventDefault()
        if (e.key === undefined || isActivationKey(e.key)) {
            a()
        }
    }

    return <div className="text-center">
        <p className="h6 mb-0">
            <i className="icon ion-ios-warning text-danger"></i>
            {Infra.strings.formatString(Infra.strings.Search.Error.CardLoad,
                <a href="#" onClick={(e) => eh(e, props.action)} onKeyPress={(e) => eh(e, props.action)}>
                    {Infra.strings.Search.Error.TryAgain}
                </a>,
                <a href="#" onClick={(e) => eh(e, props.editQueryAction)} 
                    onKeyPress={(e) => eh(e, props.editQueryAction)}>
                    {Infra.strings.Search.Error.GoBackToQueryEditor}
                </a>
            )}
        </p>
    </div>
}

function getConfig() {
    const idxFilesNodes = document.querySelectorAll("meta[name=x-panther-index-discovery]")
    const idxFiles = []
    for (let i = 0; i < idxFilesNodes.length; i++) {
        idxFiles.push(idxFilesNodes[i].content)
    }

    const dictFilesNodes = document.querySelectorAll("meta[name=x-panther-dictionary-discovery]")
    const dictFiles = []
    for (let i = 0; i < dictFilesNodes.length; i++) {
        dictFiles.push(dictFilesNodes[i].content)
    }

    return {indexes: idxFiles, dictionaries: dictFiles}
}

export function initializeSearch() {
    const apiType = document.querySelector("meta[name=x-panther-api]").content
    const context = new PASearchContext(apiType)
    const cfg = getConfig()

    context.reloadSchema(cfg.indexes, cfg.dictionaries).then(() => {
        if (context.schema && context.dictionary) {
            context.performFirstLoadStateRestoration()
        }
    })
    console.debug("The Panther context is:", context)
    console.debug("Happy debugging!")
}
