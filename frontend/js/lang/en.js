export default {
    "Card image": "Card image",
    CostumeThumbAlt: "Costume icon",

    CISwitch: {
        ExitGalleryMode: "Exit Gallery Mode",
        Option: {
            Normal: "Normal",
            Idolized: "Idolized",
            Both: "Both",
        }
    },

    CDM: {
        Title: "Layout",
        SwitchHint: "Esports mode: only show stats. Gallery mode hides stats so you can enjoy the art.",
        Option: {
            Normal: "Normal",
            Esports: "Esports",
            Gallery: "Gallery",
        }
    },

    TTNode: {
        VOICE: "VOICE",
        STORY: "STORY",
        AWAKEN: "AWAKEN",
        COSTUME: "COSTUME",
        ACTIVE: "SKILL",
        INSPIRE: "INSIGHT",
        PASSIVE: "ABILITY",
        START: "START",
    },

    "TTWrapper.NIntermediates": "{0} intermediates",
    "Unlock Requirements:": "Unlock Requirements:",
    "TTWrapper.CardRank": "Limit Break: {0}",
    "TTWrapper.CardRankShort": "LB: {0}",
    "TTWrapper.ResetWarning": "Really reset skill tree data? This operation cannot be undone.",
    "TTWrapper.ResetConfirm": "Reset",
    "TTWrapper.ResetCancel": "Cancel",
    "TTWrapper.UnlockHint": "Double-click a node to unlock it. This information is saved in your browser.",
    "Reset All Nodes...": "Reset All Nodes...",
    "TTWrapper.ExpandSkillTree": "Expand skill tree",
    "TTWrapper.WaitingOnServerForTTData": "Loading skill tree information... Please wait.",
    "TTWrapper.FailedToRetrieveTTFromServer": "Could not load the skill tree. Try reloading the page.",
    "TLInject.InputFieldPlaceholder": "Translation...",
    "TLInject.HelpText": "Please review the {0} before you submit anything.",
    "TLInject.HelpLinkPlaceholder": "translation guidelines",
    "TLInject.Submit": "Submit",
    "TLInject.Cancel": "Cancel",
    "TLInject.ExplicitClear": "Remove Translation",
    "TLInject.SubmissionPrompt": "What is the {0} translation of \"{1}\"?",
    "TLInject.CurrentSubmissionIsMock": "This is only a demo. The phrase you submit will only be displayed for you.",
    "TLInject.localizedLanguages": {
        en: "English",
        ja: "Japanese",
    },
    SST: {
        LoadingPleaseWait: "Please wait while the script loads...",
        Header: "Story Transcript",
        PlayerName: "You"
    },
    Saint: {
        HeaderCurrentTiers: "Cutoffs",
        DatasetNameFormat: "Top {0} ({1})",
        DatasetNameFormatHigh: "Rank {0}",
        DatasetFriendlyName: {
            Voltage: "Voltage",
            Points: "Points",
        },
        RankTypeSwitchLabel: "Ranking",
        EnterEditMode: "Edit",
        ExitEditMode: "Done",
        PointCount: "{0} pts",
        TrendingUp: "Trending up (+{0} from last delta)",
        TrendingDown: "Trending down ({0} from last delta)",
        UpdateTime: "Last cutoff update: {1}. Last check-in with server: {0}",
        UpdateTimeNote: "Updated automatically.",
        UpdatesDisabled: "The event has ended.",
        GraphPeriodLabel: "Period",
        GraphPeriod: {
            Hours: "{0}h",
            Days: "{0}d",
            All: "All",
        }
    },
    SendFeedback: {
        ModalTitle: "Send Feedback",
        PlaceholderText: "This form is anonymous, so you won't receive a response unless you enter contact info.",
        Send: "Send",
        Cancel: "Cancel"
    },
    LangMenu: {
        DictionaryFormat: "{0} ({1})",
        ModalTitle: "Language Settings",
        UILanguageSelectLabel: "Use this language for site navigation:",
        DictionarySelectLabel: "Use this language for game data:",
        Save: "Save",
        Cancel: "Cancel",
        GoToExperiments: "Experiments",
        RegionSelectLabel: "Prefer this server when viewing news or the event tracker:",
    },
    StoragePermission: {
        RequestTitle: "Storage Permission Required",
        RequestBody: [
            `In order for this feature to work, I need to store some information (commonly known as "cookies")
                in your browser. The stored information is for technical purposes only and cannot be used to 
                identify you, and it is not shared with third parties.`,
            `If you deny permission, the site will still work. 
                I'll ask again next time you use a feature that requires storage.`
        ],
        AllowButton: "Allow",
        DenyButton: "Deny",
    },
    Search: {
        PaginationTitle: "Page",
        RemoveCriteria: "Delete",
        CriteriaBlocksTitle: "Add filters to your search:",
        SortBy: "Sort By",
        SortDesc: "(High to Low)",
        SortAsc: "(Low to High)",
        TextBoxSRLabel: "Search Box",
        TextBoxHint: "Find filters...",
        ButtonLabel: "Search",
        SchemaLoadErrorTryAgain: "Try again",
        EnumPlaceholder: "Choose one...",
        Operator: {
            Equals: "=",
            LessThan: "<",
            GreaterThan: ">",
            LessThanEqual: "≤",
            GreaterThanEqual: "≥",
        },
        DismissErrorModal: "Dismiss",
        Error: {
            NoCriteriaValues: `You need to add some filters before searching. 
                Add filters by typing in the search box, or by selecting them from the grid.`,
            SchemaLoad: "There was a network error while acquiring filter info. {0}?",
            CardLoad: "There was a network error while loading card displays. {0}, or {1}.",
            ExecuteFailed: "The server could not complete your search. The error code it returned was: {0}.",
            NoResults: "Could not find any results. Please check your filters.",
            TryAgain: "Try again",
            GoBackToQueryEditor: "edit your query",
            CompletionistUnsupported: "Typing suggestions aren't supported for the current language. Sorry."
        },
        PurgatoryDescriptionHighlightedPart: "Notice: ",
        PurgatoryDescription: "I removed the \"{0}\" filter because it was mutually exclusive with \"{1}\".",
        RestorePurgatoryLabel: "Undo",
        StateMessage: {
            Continue: "Continue Searching",
            LoadingSchema: "Acquiring filter info...",
            Searching: "Performing search...",
            LoadingCards: "Preparing card displays...",
        },
        NumResultsLabel: "{0}. You can share this search by copying the link from your browser's address bar.",
        NumResultsFormat: (n /* : int */) => {
            switch (n) {
            case 1: return `${n} result`
            default: return `${n} results`
            }
        },
    }
}
