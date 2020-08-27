import XXH from "xxhashjs"

const kNodeIDSlot = 0
const kNodeDepthSlot = 1
const kNodeParentSlot = 2
const kNodeVerticalSlot = 3

const kNodeConnectionBack = 100
const kNodeConnectionDown = 101
const kNodeConnectionUp = 102

class WFCBitSet {
    constructor(size, src = undefined) {
        if (src) {
            this.backing = Uint32Array.from(src)
        } else {
            this.backing = new Uint32Array(Math.ceil(size / 32))
        }
    }

    bit(pos) {
        const word = (pos / 32) | 0
        return (this.backing[word] & (1 << (pos % 32)))? 1 : 0
    }

    set(pos, v) {
        const word = (pos / 32) | 0
        this.backing[word] |= v << (pos % 32)
    }

    inert() {
        return Array.from(this.backing)
    }
}

export class TTDataAccess {
    constructor(stack) {
        this.ttID = stack.id

        const construct = TTDataAccess.createShape(stack)
        this.graph = construct.nodes
        this.startNode = construct.start
        this.shapeId = XXH.h32(JSON.stringify(this.graph), 0x11112222).toString(16)
        this.tree = stack.tree
        this.itemSets = stack.item_sets
        this.lockMap = stack.lock_levels
        this.matrixHeight = stack.tree[0].length

        this.lockMap.sort((a, b) => a[0] - b[0])
    }

    static createShape(stack) {
        const nodes = []
        let start = undefined

        for (let i = 0, j = -1; i < stack.tree.length; ++i, ++j) {
            const cur = stack.tree[i]
            const prv = j < 0? [] : stack.tree[j]

            for (let k = 0; k < cur.length; ++k) {
                if (!cur[k]) {
                    continue
                }

                let thisNode = [cur[k][0], i]
                if (cur[k][1] == kNodeConnectionBack && prv[k]) {
                    thisNode.push(prv[k][0])
                }
                if (cur[k][1] == kNodeConnectionDown && k + 1 < cur.length && cur[k + 1]) {
                    thisNode.push(cur[k + 1][0])
                }
                if (cur[k][1] == kNodeConnectionUp && k - 1 > 0 && cur[k - 1]) {
                    thisNode.push(cur[k - 1][0])
                }

                if (cur[k][2].type == 1) {
                    start = cur[k][0]
                    if (thisNode.length < 3) {
                        thisNode.push(null)
                    }
                    console.debug(`Found the start node: id ${start}.`)
                }

                if (thisNode.length < 3) {
                    console.warn(thisNode, "no parent?")
                }

                thisNode.push(k)
                nodes.push(thisNode)
            }
        }

        nodes.sort((a, b) => a[0] - b[0])
        return {start, nodes}
    }

    static fastFind(inArray, value, extract = (x) => x) {
        let lo = 0
        let hi = inArray.length
        while (lo != hi) {
            const i = lo + (((hi - lo) / 2) | 0)
            let piv = extract(inArray[i])
            if (piv === value) {
                return inArray[i]
            }

            if (piv > value) {
                hi = i
            } else {
                lo = i + 1
            }
        }
        return undefined
    }

    // Calculate the path from fromNode to toNode.
    // Returned as the list of nodes to go through, but not in path order.
    path(fromNode, toNode) {
        const nodeId = (x) => x[kNodeIDSlot]
        // TODO: getting rid of some of these fastFinds is low-hanging optimization fruit.
        // You will probably have to make the tree double linked though.
        let srcStep = TTDataAccess.fastFind(this.graph, fromNode, nodeId)
        let dstStep = TTDataAccess.fastFind(this.graph, toNode, nodeId)

        let srcPath = []
        let dstPath = []
        while (srcStep[kNodeIDSlot] !== dstStep[kNodeIDSlot]) {
            if (dstStep[kNodeDepthSlot] >= srcStep[kNodeDepthSlot]) {
                dstPath.push(dstStep[kNodeIDSlot])
                dstStep = TTDataAccess.fastFind(this.graph, dstStep[kNodeParentSlot], nodeId)
            } else {
                srcPath.push(srcStep[kNodeIDSlot])
                srcStep = TTDataAccess.fastFind(this.graph, srcStep[kNodeParentSlot], nodeId)
            }
        }

        dstPath.reverse()
        if (dstPath[0] === srcPath[srcPath.length - 1]) {
            srcPath.pop()
        }
        dstPath.forEach((v) => srcPath.push(v))
        srcPath.sort((a, b) => a - b)
        return srcPath
    }

    sumCostForPath(path) {
        let maxGrade = 0
        let goldCost = 0
        const sum = []
        const sumItems = {}

        for (let i = 0; i < path.length; ++i) {
            const pos = TTDataAccess.fastFind(this.graph, path[i], (x) => x[kNodeIDSlot])
            const nodeInfo = this.tree[pos[kNodeDepthSlot]][pos[kNodeVerticalSlot]]
            const itemSet = this.itemSets.sets[nodeInfo[2].req_mats]

            if (nodeInfo[2].req_grade > maxGrade) {
                maxGrade = nodeInfo[2].req_grade
            }

            for (const itemNumber in itemSet) {
                if (!Object.hasOwnProperty.call(itemSet, itemNumber)) {
                    continue
                }

                if (itemNumber === "_gold") {
                    goldCost += itemSet[itemNumber]
                    continue
                }

                if (itemNumber in sumItems) {
                    sumItems[itemNumber] += itemSet[itemNumber]
                } else {
                    sumItems[itemNumber] = itemSet[itemNumber]
                    sum.push(itemNumber)
                }
            }
        }

        return {
            materials: sum.sort((a, b) => {
                return this.itemSets.items[a][1] - this.itemSets.items[b][1]
            }).map((iid) => {
                return {count: sumItems[iid], image: this.itemSets.items[iid][0]}
            }),
            gold: goldCost,
            grade: maxGrade,
        }
    }

    lockGradeForLevel(l) {
        const ent = TTDataAccess.fastFind(this.lockMap, l, (x) => x[0])
        if (ent) {
            return ent[1]
        }
        return undefined
    }

    getNodeByID(aNode) {
        const nI = TTDataAccess.fastFind(this.graph, aNode, (x) => x[0])
        const depth = nI[kNodeDepthSlot]
        const vert = nI[kNodeVerticalSlot]
        return this.tree[depth][vert]? this.tree[depth][vert][2] : null
    }
}

export class TTUserConfiguration {
    constructor(dataAccess) {
        this.dataAccess = dataAccess
        this.state = null
        this.dirty = false
        this._awakeFromLocalStorage()
    }

    _awakeFromLocalStorage() {
        const h = localStorage.getItem(`as$trainingtree$${this.dataAccess.ttID}`)
        if (h) {
            this.state = JSON.parse(h)
            if (this.state.shapeId === this.dataAccess.shapeId) {
                this.state.active = new WFCBitSet(0, this.state.active)
                return
            }
            console.debug("Tree shape hash changed, abandoning saved state.")
        }

        this.resetState(false)
    }

    _saveToLocalStorage() {
        if (this.dirty) {
            const freeze = {
                heads: this.state.heads,
                active: this.state.active.inert(),
                shapeId: this.dataAccess.shapeId
            }
            localStorage.setItem(`as$trainingtree$${this.dataAccess.ttID}`, JSON.stringify(freeze))
            this.dirty = false
        }
    }

    _clearFromLocalStorage() {
        localStorage.removeItem(`as$trainingtree$${this.dataAccess.ttID}`)
    }

    isNodeActive(depth, vert) {
        return this.state.active.bit(depth * this.dataAccess.matrixHeight + vert) == 1
    }

    isNodeActiveByID(aNode) {
        const nI = TTDataAccess.fastFind(this.dataAccess.graph, aNode, (x) => x[0])
        const depth = nI[kNodeDepthSlot]
        const vert = nI[kNodeVerticalSlot]
        return this.isNodeActive(depth, vert)
    }

    calculateStatContributionOfActiveNodes() {
        let appeal = 0, stamina = 0, technical = 0, isIdolized = false
        for (let i = 0; i < this.dataAccess.graph.length; ++i) {
            const nI = this.dataAccess.graph[i]
            const depth = nI[kNodeDepthSlot]
            const vert = nI[kNodeVerticalSlot]

            if (!this.isNodeActive(depth, vert)) {
                continue
            }

            const real = this.dataAccess.tree[depth][vert][2]
            if (real.type == 2) {
                switch(real.stat) {
                case 2: stamina += real.value; break
                case 3: appeal += real.value; break
                case 4: technical += real.value; break
                }
            }
            if (real.type == 5) {
                isIdolized = true
            }
        }

        return {appeal, stamina, technical, isIdolized}
    }

    // Checks if the node is a head based on the current active bitmap.
    // A node is a head if it is possible to find an inactive child by traversing through it.
    // So this method checks each possible direction - if all are selected, it's not a head.
    isHead(aNode) {
        const nI = TTDataAccess.fastFind(this.dataAccess.graph, aNode, (x) => x[0])
        const depth = nI[kNodeDepthSlot]
        const vert = nI[kNodeVerticalSlot]

        const nodeForward = depth + 1 < this.dataAccess.tree.length?
            this.dataAccess.tree[depth + 1][nI[kNodeVerticalSlot]] : undefined
        const nodeUp = vert > 0?
            this.dataAccess.tree[depth][vert - 1] : undefined
        const nodeDown = vert + 1 < this.dataAccess.tree[depth].length?
            this.dataAccess.tree[depth][vert + 1] : undefined

        let nChild = 0
        let nConnected = 0
        if (nodeUp && nodeUp[1] == kNodeConnectionDown) {
            nChild++
            if (this.state.active.bit((depth * this.dataAccess.matrixHeight) + vert - 1)) {
                nConnected++
            }
        }
        if (nodeDown && nodeDown[1] == kNodeConnectionUp) {
            nChild++
            if (this.state.active.bit((depth * this.dataAccess.matrixHeight) + vert + 1)) {
                nConnected++
            }
        }
        if (nodeForward && nodeForward[1] == kNodeConnectionBack) {
            nChild++
            if (this.state.active.bit((depth + 1) * this.dataAccess.matrixHeight + vert)) {
                nConnected++
            }
        }

        if (nChild === nConnected) {
            return false
        }
        return true
    }

    // Update the active bitmap so the set of nodes is selected.
    // To do that we need to recalculate the set of heads.
    // Currently commits to local storage immediately, but at some point
    // a debounce should be added.
    activateSet(nodes) {
        nodes.forEach((nId) => {
            const gNode = TTDataAccess.fastFind(this.dataAccess.graph, nId, (x) => x[0])
            this.state.active.set(gNode[kNodeDepthSlot] * this.dataAccess.matrixHeight + gNode[kNodeVerticalSlot], 1)
        })

        for (let i = 0; i < this.state.heads.length; ++i) {
            if (!this.isHead(this.state.heads[i])) {
                this.state.heads.splice(i, 1)
                i--
            }
        }
        nodes.forEach((v) => {
            if (this.isHead(v)) {
                this.state.heads.push(v)
            }
        })

        console.debug("Heads", this.state.heads)
        console.debug("ABM", this.state.active)
        this.dirty = true

        this._saveToLocalStorage()
    }

    // Find the shortest path to toNode from any of the graph heads.
    // TODO: currently uses a dumb head selection method - maybe a heuristic (e.g. based on
    // depth would be better?)
    pathFromAnyHead(toNode) {
        let minPath = null
        for (let i = 0; i < this.state.heads.length; i++) {
            const head = this.state.heads[i]
            const path = this.dataAccess.path(head, toNode)
            if (minPath === null || path.length < minPath.length) {
                minPath = path
            }
        }

        return minPath
    }

    resetState(needSave = true) {
        this.state = {
            /* Heads are all active nodes where you can reach inactive children by traversing through them.
             * In other words, any active node whose children aren't all active.
             */
            heads: [this.dataAccess.startNode],
            // Unlike the graph which is a proper tree, this is a 5 x n bool matrix where the
            // cells represent the nodes' transposed UI layout.
            /* (Cells are rendered staggered as they appear in game, so the representation
             *  looks more like this...)
             *  SkillTree rendering:          Matrix representation
             *    A B C D                     A E I M Q  depth
             *   E F G H                      B F J N R   |
             *  I J K L                       C G K O S   V
             *   M N O P                      D H L P T
             *    Q R S T                     vert ->
             * You can calculate the node's flat coordinate in the bitset as depth * height + vert.
             */
            active: new WFCBitSet(this.dataAccess.tree.length * this.dataAccess.matrixHeight)
            // shapeId
        }

        const d = TTDataAccess.fastFind(this.dataAccess.graph, this.dataAccess.startNode, (x) => x[kNodeIDSlot])
        this.state.active.set((d[kNodeDepthSlot] * this.dataAccess.tree[0].length) + d[kNodeVerticalSlot], 1)
        console.debug("TTUserConfiguration: init fresh for", this.dataAccess.ttID)

        if (needSave) {
            this._clearFromLocalStorage()
            this.dirty = false
        }
    }
}