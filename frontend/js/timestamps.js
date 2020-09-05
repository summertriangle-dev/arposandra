function pad2(n) {
    if (n < 10) {
        return `0${n}`
    }
    return "" + n
}

function formatTime(ts, style) {
    const d = new Date(ts * 1000)
    switch(style) {
    case "time":
        return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
    case "date":
        return `${d.getFullYear()}/${pad2(d.getMonth() + 1)}/${pad2(d.getDate())}`
    case "fullshort":
        return `${pad2(d.getMonth() + 1)}/${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`
    case "full":
    default:
        return `${d.getFullYear()}/${pad2(d.getMonth() + 1)}/${pad2(d.getDate())} ` + 
            `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
    }
}

function formatTooltipTime(ts, tz) {
    const d = new Date(ts * 1000)
    return `${d.getUTCFullYear()}/${pad2(d.getUTCMonth() + 1)}/${pad2(d.getUTCDate())} ` + 
            `${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())} ${tz}`
}

function swapTimeOnClick(e) {
    const n = e.target
    if (!n.dataset.origOffset) {
        return
    }

    if (n.getAttribute("tsi-swapped")) {
        n.removeAttribute("tsi-swapped")
        n.textContent = formatTime(parseInt(n.dataset.ts), n.dataset.style)
    } else {
        const cmp = n.dataset.origOffset.split(",")
        const offset = parseInt(cmp[0]), tz = cmp[1]
        n.setAttribute("tsi-swapped", 1)
        n.textContent = formatTooltipTime(parseInt(n.dataset.ts) + offset, tz)
    }
}

export function initialize() {
    console.debug("timestamps.js: start")
    const nodes = document.getElementsByClassName("kars-data-ts")
    for (let i = 0; i < nodes.length; ++i) {
        const n = nodes[i]
        n.textContent = formatTime(parseInt(n.dataset.ts), n.dataset.style)

        if (n.dataset.origOffset) {
            const cmp = n.dataset.origOffset.split(",")
            const offset = parseInt(cmp[0]), tz = cmp[1]
            n.title = formatTooltipTime(parseInt(n.dataset.ts) + offset, tz)
        }

        n.addEventListener("click", swapTimeOnClick, {passive: true})
    }
}