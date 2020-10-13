const MatchValueForAutoSetApplyType = {
    "member_group": 6, 
    "member_subunit": 5, 
    "member_year": 7, 
    "role": 3,
    "attribute": 4,
}

const CanAutoSetApplyTypeKeys = Object.keys(MatchValueForAutoSetApplyType).slice(0)

export class CardSearchDomainExpert {
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
