const MatchValueForAutoSetApplyType = {
    "member_group": 7, 
    "member_subunit": 6, 
    "member_year": 8, 
    "role": 4,
    "attribute": 5,
}

const CanAutoSetApplyTypeKeys = Object.keys(MatchValueForAutoSetApplyType).slice(0)

export class PACardSearchDomainExpert {
    async sendAjaxRequest(objectIds) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.responseType = "document"
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(xhr.responseXML)
                } else {
                    reject(xhr.status)
                }
            }
            xhr.open("GET", "/api/private/cards/ajax/" + objectIds.join(","))
            xhr.send()
        })
    }

    async sendSearchRequest(withParams) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText)
                        reject({error: err.error})
                        return
                    } catch {
                        reject({error: `http(${xhr.status})`})
                        return
                    }
                }
            }
            xhr.open("POST", "/api/private/search/cards/results.json")
            xhr.setRequestHeader("Content-Type", "application/json")
            xhr.send(JSON.stringify(withParams))
        })
    }

    didAddCriteria(context, addedCriteria, proposedState) {
        if (addedCriteria === "skills.apply_type") {
            if (!proposedState.queryValues) {
                const addValues = {}
                Object.assign(addValues, context.state.queryValues)
                proposedState.queryValues = addValues
            }

            const keys = Object.keys(proposedState.queryValues)
            for (let key in keys) {
                if (CanAutoSetApplyTypeKeys.includes(keys[key])) {
                    proposedState.queryValues[addedCriteria] = MatchValueForAutoSetApplyType[keys[key]]
                    break
                }
            }
        }

        return proposedState
    }

    didChangeCriteria(context, addedCriteria, proposedState) {
        return proposedState
    }
}

export class PAAccessorySearchDomainExpert {
    async sendAjaxRequest(objectIds) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.responseType = "document"
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(xhr.responseXML)
                } else {
                    reject(xhr.status)
                }
            }
            xhr.open("GET", "/api/private/accessories/ajax/" + objectIds.join(","))
            xhr.send()
        })
    }

    async sendSearchRequest(withParams) {
        return await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.onreadystatechange = () => {
                if (xhr.readyState != 4) {
                    return
                }

                if (xhr.status == 200) {
                    resolve(JSON.parse(xhr.responseText))
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText)
                        reject({error: err.error})
                        return
                    } catch {
                        reject({error: `http(${xhr.status})`})
                        return
                    }
                }
            }
            xhr.open("POST", "/api/private/search/accessories/results.json")
            xhr.setRequestHeader("Content-Type", "application/json")
            xhr.send(JSON.stringify(withParams))
        })
    }
}
