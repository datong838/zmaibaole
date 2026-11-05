/* Offline reviewed site policy. No policy changes through HTTP or page messages. */
globalThis.DOM_EXPORT_POLICY = Object.freeze({
  origin: "https://life.douyin.com",
  // Observed governance DOM, 2026-10-21; actions remain read/query only.
  governanceCenter: Object.freeze({path:'/p/governance/home_violation_center',recordsPath:'/p/governance/violation_list',rootId:'governanceRoot',
      recordsTable:'governance_merchant-Table-Implement',recordsRow:'governance_merchant-Table-Row',recordsLink:'link-gpKMLO',
      calendar:'governance_merchant-date-picker-popper',calendarView:'governance_merchant-date-view',calendarDay:'governance_merchant-date-col',
    datePlaceholder:'开始日期 ～ 结束日期',dateRoot:'governance_merchant-date-picker',dateRange:'governance_merchant-date-picker-range',
    topList:'topList-DDjs8Y',topTitle:'title-KYD1nB',viewAll:'viewAllText-W89JWE',
    tools:'todoSummary-xpJGcr',toolItem:'todoItem-SQ0SNc',toolLabel:'todoLabel-I3rSqB',
    pagination:'pagination-D3lzMl',pagerItem:'governance_merchant-pager-item',pagerDisabled:'governance_merchant-pager-item-disabled',pagerChecked:'governance_merchant-pager-item-checked'}),
  // Exact names only. A newly encountered site control MUST be reviewed offline.
  clicks: [
    {name: "立即体验", role: "button", kind: "onboarding-dismiss"},
    {name: "违规中心", kind: "navigation"},
    {name: "经营保障", kind: "navigation"},
    {name: "中差评（1-3心）", kind: "filter"},
    {name: "查看投诉结果", kind: "complaint-read"},
    {name: "投诉审核中", kind: "complaint-read"},
    {name: "投诉", kind: "complaint-draft"},
    {name: "评价管理", kind: "navigation"},
    {name: "全部评价 4367", kind: "navigation"},
    {name: "服务商7576493388812273702", kind: "navigation"},
    {name: "切换公司", role: "button", kind: "navigation"},
    {name: "切换", role: "button", kind: "navigation"},
    {name: "烟台一成教育文化咨询有限公司", kind: "company"},
    {name: "上海老芗汇餐饮管理有限公司", kind: "company"},
    {name: "确认", role: "button", kind: "company-confirm"},
    {name: "评价时间", role: "textbox", kind: "filter"},
    {name: "导出", kind: "export"},
    {name: "导出评价", kind: "export"},
    {name: "评价导出记录", kind: "export"},
    {name: "下载", kind: "download"},
    {name: "取消", role: "button", kind: "dismiss"},
    // 2026-10-20 offline review: date-range picker month navigation (read-only calendar UI).
    // "9月" = month title in the picker header (opens month grid); "10月" = month cell
    // inside that grid. Both are pure calendar navigation, same trust level as day cells.
    {name: "9月", kind: "filter"},
    {name: "10月", kind: "filter"}
  ],
  filterPlaceholders: ["搜索商户", "请选择日期范围，不选则为近一年"],
  // Calendar clicks additionally require this structural parent from inspected UI DOM.
  dateCellSelector: ".byted-date-col.byted-date-date",
  downloadExtensions: ["xlsx", "xls", "csv", "zip"],
  maxNodes: 4000,
  maxText: 800
});
