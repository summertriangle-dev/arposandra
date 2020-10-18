import React from "react"

export function isCompletionistSupported(lang) {
    return false
}

function fastFind(inArray, value) {
    let lo = 0
    let hi = inArray.length
    while (lo != hi) {
        const i = lo + (((hi - lo) / 2) | 0)
        let piv = inArray[i]
        if (piv === value) {
            return i
        }

        if (piv > value) {
            hi = i
        } else {
            lo = i + 1
        }
    }
    return lo
}

function last(a) {
    return a[a.length - 1]
}

export class PAWordCompletionist extends React.Component {
    constructor(props) {
        super(props)
    }

    computeMatches() {
        const matches = []
        const lastWord = last(this.props.partial.split(/\s/))
        if (!lastWord) {
            return []
        }

        const firstIndex = fastFind(this.props.dictionary.words, lastWord)

        for (let i = firstIndex; i < this.props.dictionary.words.length; ++i) {
            const word = this.props.dictionary.words[i]
            if (word.startsWith(lastWord)) {
                matches.push(word)
            } else {
                break
            }
        }

        return matches
    }

    render() {
        const words = this.computeMatches()
        if (words.length == 0) {
            return null
        }

        return <ul className="search-completions">
            {words.map((x) => {
                return <li className="completion" key={x}>{x}</li>
            })}
        </ul>
    }
}