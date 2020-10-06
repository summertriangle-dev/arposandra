import React from "react"
import Infra from "../infra"

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

export class PAEnumField extends React.Component {
    constructor(props) {
        super(props)
    }

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
        this.state = {compare_type: "eq", compare_to: null}
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
                    placeholder={this.props.criteria.display_name} 
                    value={this.state.compare_to || ""}
                    onChange={(event) => this.acceptInput(event)} />
            </div>    
        </>
    }
}