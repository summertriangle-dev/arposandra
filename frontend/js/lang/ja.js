export default {
    "Card image": "カード画像",
    CostumeThumbAlt: "Costume icon",

    CISwitch: {
        ExitGalleryMode: "ギャラリーモードを終了",
        Option: {
            Normal: "基本",
            Idolized: "覚醒",
            Both: "両方",
        }
    },
    CDM: {
        Title: "レイアウト",
        SwitchHint: "戦術モード: パラメータのみを表示。ギャラリーモード: 画像のみを表示",
        Option: {
            Normal: "通常",
            Esports: "戦術",
            Gallery: "ギャラリー",
        }
    },
    TTNode: {
        VOICE: "ボイス",
        STORY: "ストーリー",
        AWAKEN: "覚醒",
        COSTUME: "衣装",
        ACTIVE: "特技",
        INSPIRE: "ひらめき",
        PASSIVE: "個性",
        START: "スタート",
    },
    "TTWrapper.NIntermediates": "{0}個の追加獲得",
    "Unlock Requirements:": "解放条件:",
    "TTWrapper.CardRank": "限界突破: {0}",
    "TTWrapper.CardRankShort": "限界突破: {0}",
    "TTWrapper.ResetWarning": "リセットしてもよろしいですか?",
    "TTWrapper.ResetConfirm": "リセット",
    "TTWrapper.ResetCancel": "キャンセル",
    "TTWrapper.UnlockHint": "パネルをダブルクリックして取得します。進行状況はブラウザに保存されます",
    "Reset All Nodes...": "全てのパネルをリセット...",
    "TTWrapper.ExpandSkillTree": "育成ツリーを広げる",
    "TTWrapper.WaitingOnServerForTTData": "育成ツリーをロード中...",
    "TTWrapper.FailedToRetrieveTTFromServer": "育成ツリーをロードに失敗しました。ページをリロードしてみてください",

    // Not needed?
    "TLInject.InputFieldPlaceholder": "Translation...",
    "TLInject.HelpText": "Please review the {0} before you submit anything.",
    "TLInject.HelpLinkPlaceholder": "translation guidelines",
    "TLInject.Submit": "Submit",
    "TLInject.Cancel": "Cancel",
    "TLInject.ExplicitClear": "Remove Translation",
    "TLInject.SubmissionPrompt": "What is the {0} translation of \"{1}\"?",
    "TLInject.CurrentSubmissionIsMock": "This is only a demo. The phrase you submit will only be displayed for you.",
    "TLInject.localizedLanguages": {
        en: "英語",
        ja: "日本語"
    },

    NewsFilter: {
        Title: "イベントとガチャのみを表示",
        Option: {
            No: "○",
            Yes: "｜",
        }
    },
    SST: {
        LoadingPleaseWait: "エピソード脚本をロード中...",
        Header: "エピソード脚本",
        PlayerName: "（あなた）"
    },
    Saint: {
        HeaderCurrentTiers: "ボーダー",
        DatasetNameFormat: "{0}位上 ({1})",
        DatasetNameFormatHigh: "Rank {0}",
        DatasetFriendlyName: {
            Voltage: "ボルテージ",
            Points: "イベントP",
        },
        RankTypeSwitchLabel: "ランキング",
        EnterEditMode: "編集",
        ExitEditMode: "完了",
        PointCount: "{0} P",
        TrendingUp: "上昇傾向 (最後の差額から: +{0})",
        TrendingDown: "下降傾向 (最後の差額から: {0})",
        UpdateTime: "最終更新(ボーダー): {1}。 最終連絡(サーバー): {0}。",
        UpdateTimeNote: "自動的に更新される。",
        UpdatesDisabled: "イベントは終了しました。",
        GraphPeriodLabel: "期間",
        GraphPeriod: {
            Hours: "{0}時",
            Days: "{0}日間",
            All: "全て",
        }
    },
    SendFeedback: {
        ModalTitle: "フィードバックを送信する",
        PlaceholderText: "このサイトの管理者は日本語を読むことができません。しかし、それが止めさせないでください。",
        Send: "参加する",
        Cancel: "キャンセル"
    },
    LangMenu: {
        DictionaryFormat: "{0} ({1})",
        ModalTitle: "言語設定",
        UILanguageSelectLabel: "Use this language for site navigation:",
        DictionarySelectLabel: "Use this language for game data:",
        Save: "Save",
        Cancel: "キャンセル",
        GoToExperiments: "実験",
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
        NumResultsLabel: "{0} results. You can share this search by copying the link from your browser's address bar."
    }
}
