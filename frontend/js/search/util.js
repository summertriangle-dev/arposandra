import { CONTROL_TYPE } from "./components"

export function serializeQuery(fromSchema, query) {
    const frags = []
    const keys = Object.keys(query)

    keys.forEach((k) => {
        const schema = fromSchema.criteria[k]
        const value = query[k]

        if (k === "_sort") {
            frags.push(`${k}=${value}`)
            return
        }

        switch(schema.type) {
        case CONTROL_TYPE.NUMBER: {
            const val = `${value.compare_type},${value.compare_to}`
            frags.push(`${k}=${encodeURIComponent(val)}`)
            break
        }
        case CONTROL_TYPE.DATETIME: {
            frags.push(`${k}=${encodeURIComponent(value.toISOString())}`)
            break
        }
        case CONTROL_TYPE.STRING:
        case CONTROL_TYPE.STRING_MAX: {
            frags.push(`${k}=${encodeURIComponent(value)}`)
            break
        }                    
        case CONTROL_TYPE.COMPOSITE:
            break
        case CONTROL_TYPE.ENUM:
        case CONTROL_TYPE.ENUM_2: {
            if (schema.behaviour && schema.behaviour.compare_type === "bit-set") {
                frags.push(`${k}=${encodeURIComponent(JSON.stringify(value))}`)
            } else {
                frags.push(`${k}=${encodeURIComponent(value)}`)
            }
            break
        }
        }
    })

    return frags.join("&")
}

function _allChoicesOf(bitList, criteria) {
    for (let i = 0; i < bitList.length; i++) {
        const e = bitList[i]
        let die = true

        for (let j = 0; j < criteria.choices.length; j++) {    
            if (criteria.choices[j].value === e) {
                die = false
                break
            }
        }

        if (die) {
            return false
        }
    }

    return true
}

export function deserializeQuery(fromSchema, fragment) {
    const frags = fragment.split("&")
    const builtQuery = {}

    frags.forEach((t) => {
        const [key, value] = decodeURIComponent(t).split("=")

        if (key === "_sort" 
            && Object.hasOwnProperty.call(fromSchema.criteria, value.substring(1)) 
            && ["-", "+"].includes(value[0])) {
            builtQuery["_sort"] = value
            return
        }

        if (!Object.hasOwnProperty.call(fromSchema.criteria, key)) {
            return
        }

        if (!key || !value) {
            return
        }

        const schema = fromSchema.criteria[key] 
        switch(schema.type) {
        case CONTROL_TYPE.NUMBER: {
            const [ct, num] = value.split(",")
            if (["lt", "gt", "eq"].includes(ct) && !isNaN(parseInt(num))) {
                builtQuery[key] = {compare_to: parseInt(num), compare_type: ct}
            }
            break
        }
        case CONTROL_TYPE.DATETIME: {
            const dts = Date.parse(value)
            if (!isNaN(dts)) {
                builtQuery[key] = new Date(dts)
            }
            break
        }
        case CONTROL_TYPE.STRING:
        case CONTROL_TYPE.STRING_MAX: {
            if (schema.max_length) {
                if (value.length <= schema.max_length) {
                    builtQuery[key] = value
                }
            } else {
                builtQuery[key] = value
            }
            break
        }                    
        case CONTROL_TYPE.COMPOSITE:
            break
        case CONTROL_TYPE.ENUM:
        case CONTROL_TYPE.ENUM_2: {
            if (schema.behaviour && schema.behaviour.compare_type === "bit-set") {
                const bitList = JSON.parse(value)
                if (Array.isArray(bitList) && _allChoicesOf(bitList, schema)) {
                    builtQuery[key] = bitList
                }
            } else {
                if (!isNaN(parseInt(value))) {
                    builtQuery[key] = parseInt(value)
                }
            }
            break
        }
        }
    })

    return builtQuery
}

export function simulatedNetworkDelay(t) {
    return new Promise((resolve) => { setTimeout(resolve, t || 1000) })
}

export function toHTMLDateInputFormat(d) {
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}` + 
        `-${d.getDate().toString().padStart(2, "0")}`
}

export function isActivationKey(key) {
    return (key === "Enter" || key === " ")
}
