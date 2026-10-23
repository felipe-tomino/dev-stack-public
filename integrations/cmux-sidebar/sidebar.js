// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (c) 2024-present Manaflow, Inc.; other contributors retain their rights.
// Derived from cmux Examples/CustomSidebars/workspaces.js at
// 9d01f956c51cd895e10e7d56b6dd7b5f6fcce625. See LICENSE.
// Modified 2026-10-18: external-data row, workspace metadata, and generated-file setup.
//
// Dia-style workspace sidebar: groups, cross-group drag, full context menus.
//
// Workspaces share ONE flat drag surface: group headers and workspace
// rows live in a single Reorderable. Headers are `fixed` (not grabbable, but
// they shift to open gaps like any row), so a workspace can be dragged
// between groups, into a group, or out to the ungrouped area in one gesture.
// The drop resolves to (container group, reorder anchor) from the flat index
// and dispatches workspace.group.add/remove + workspace.reorder.
//
// Group collapse is optimistic (a local signal flips instantly) and syncs via
// workspace.group.collapse/expand so the built-in sidebar agrees.
//
// Source template, not an installable sidebar on its own. producer.py prepends
// snapshot, placement, and local sidebar preferences before publishing the generated JS.
// Edit externalDataRow() below to customize the independent local-data card.

// --- optimistic UI -------------------------------------------------------------
// Every user action flips local state the same frame; the cmux command runs
// behind it and the authoritative data context (which refreshes about once a
// second) reconciles: each override clears itself as soon as the data agrees.
let selectOverride = null;
const [selectTick, setSelectTick] = signal(0);

function isSelected(w) {
  selectTick();
  if (!w) return false;
  if (selectOverride) {
    if (data.selectedId() === selectOverride) selectOverride = null; // caught up
    else return w.id === selectOverride;
  }
  return !!w.selected;
}

function selectWorkspace(id) {
  if (!id) return;
  selectOverride = id;
  setSelectTick(selectTick() + 1);
  cmux("workspace.select", { workspace_id: id });
}

const closedOverride = new Set();
const [closeTick, setCloseTick] = signal(0);

// Optimistic tabs order: a bulk drop rearranges rows locally the same frame
// (reorder_many echoes ~1s later); clears itself once the data agrees.
let orderOverride = null;
const [orderTick, setOrderTick] = signal(0);

function setOrderOverride(ids) {
  orderOverride = ids;
  setOrderTick(orderTick() + 1);
}

function visibleWorkspaces() {
  closeTick();
  orderTick();
  let ws = data.workspaces() ?? [];
  for (const id of Array.from(closedOverride)) {
    if (!ws.some((w) => w.id === id)) closedOverride.delete(id); // caught up
  }
  ws = ws.filter((w) => !closedOverride.has(w.id));
  if (orderOverride) {
    const actual = ws.map((w) => w.id).join(",");
    const wanted = orderOverride.filter((id) => ws.some((w) => w.id === id)).join(",");
    if (actual === wanted) {
      orderOverride = null; // caught up
    } else {
      const rank = new Map(orderOverride.map((id, i) => [id, i]));
      ws = [...ws].sort((a, b) => (rank.get(a.id) ?? 1e9) - (rank.get(b.id) ?? 1e9));
    }
  }
  return ws;
}

function closeWorkspace(id) {
  closedOverride.add(id);
  setCloseTick(closeTick() + 1);
  cmux("workspace.close", { workspace_id: id });
}

// Multi-select: Cmd-click toggles, Shift-click extends from the last click
// over the visible row order, plain click clears. The selection drives the
// context menu's bulk actions (group together, move, close).
const multiSelected = new Set();
const [multiTick, setMultiTick] = signal(0);
let lastClickedId = null;

function isMultiSelected(w) {
  multiTick();
  return !!w && multiSelected.has(w.id);
}

function clearMultiSelect() {
  if (multiSelected.size === 0) return;
  multiSelected.clear();
  setMultiTick(multiTick() + 1);
}

function visibleRowIds() {
  return flatEntries().filter((e) => e.kind === "ws").map((e) => e.wsId);
}

function handleRowClick(w, payload) {
  const id = w.id;
  if (payload && payload.cmd) {
    if (multiSelected.has(id)) multiSelected.delete(id);
    else multiSelected.add(id);
    setMultiTick(multiTick() + 1);
  } else if (payload && payload.shift && lastClickedId) {
    const order = visibleRowIds();
    const a = order.indexOf(lastClickedId);
    const b = order.indexOf(id);
    if (a >= 0 && b >= 0) {
      for (const rid of order.slice(Math.min(a, b), Math.max(a, b) + 1)) multiSelected.add(rid);
      setMultiTick(multiTick() + 1);
    }
  } else {
    clearMultiSelect();
    selectWorkspace(id);
  }
  lastClickedId = id;
}

// The set of workspaces a bulk menu action applies to: the multi-selection
// when the clicked row is part of it, else just the clicked row.
function bulkIds(w) {
  multiTick();
  if (w && multiSelected.has(w.id)) return Array.from(multiSelected);
  return w ? [w.id] : [];
}

const titleOverride = new Map();
const [titleTick, setTitleTick] = signal(0);

function displayTitle(w) {
  titleTick();
  if (!w) return "";
  if (titleOverride.has(w.id)) {
    const t = titleOverride.get(w.id);
    if (w.title === t) titleOverride.delete(w.id); // caught up
    else return t;
  }
  return w.title;
}

// --- inline rename -----------------------------------------------------------
// Double-click a row/header (or its Rename menu item) to edit in place.
// Editing swaps the entry's key, so the keyed reconciler remounts the row as
// an editor; Return commits through workspace(.group).rename, Escape cancels.
const [editingId, setEditingId] = signal(null);

// --- optimistic collapse -----------------------------------------------------
const collapseOverride = new Map();
const [collapseTick, setCollapseTick] = signal(0);

function isCollapsed(g) {
  collapseTick();
  if (collapseOverride.has(g.id)) {
    const v = collapseOverride.get(g.id);
    if (v === g.collapsed) collapseOverride.delete(g.id); // host caught up
    else return v;
  }
  return g.collapsed;
}

function toggleCollapse(g) {
  const next = !isCollapsed(g);
  collapseOverride.set(g.id, next);
  setCollapseTick(collapseTick() + 1);
  cmux(next ? "workspace.group.collapse" : "workspace.group.expand", { group_id: g.id });
}

// --- data helpers ------------------------------------------------------------
const groupById = (id) => (data.groups() ?? []).find((g) => g.id === id);
const membersOf = (id) => visibleWorkspaces().filter((w) => w.group === id);
// The anchor workspace IS the header (matching the built-in sidebar).
const memberRowsOf = (id) => {
  const g = groupById(id);
  return membersOf(id).filter((w) => !g || w.id !== g.anchorId);
};

// One flat entry list. A group renders (header + expanded member rows) at
// its ANCHOR's tabs position - the app's canonical block position - so a
// stray member sitting early in the tabs order can never yank the whole
// group upward. Pinned groups and pinned ungrouped workspaces float to a
// cluster at the top.
const flatEntries = computed(() => {
  const ws = visibleWorkspaces();
  const groups = new Map((data.groups() ?? []).map((g) => [g.id, g]));
  const editing = editingId();
  const wsEntry = (w, groupId) => ({
    kind: "ws",
    id: w.id + (editing === w.id ? ":edit" : ""),
    wsId: w.id,
    editing: editing === w.id,
    groupId,
  });
  const groupSection = (g) => {
    const out = [{
      kind: "header",
      id: "h:" + g.id + (editing === "h:" + g.id ? ":edit" : ""),
      groupId: g.id,
      editing: editing === "h:" + g.id,
    }];
    if (!isCollapsed(g)) {
      for (const m of memberRowsOf(g.id)) out.push(wsEntry(m, g.id));
    }
    return out;
  };

  const pinned = [];
  const rest = [];
  const seen = new Set();
  for (const w of ws) {
    if (w.group && groups.has(w.group)) {
      const g = groups.get(w.group);
      // Emit the group at its anchor's position; a group whose anchor is
      // hidden (optimistically closed) falls back to its first member.
      const isAnchor = w.id === g.anchorId || !ws.some((x) => x.id === g.anchorId);
      if (seen.has(g.id) || !isAnchor) continue;
      seen.add(g.id);
      (g.pinned ? pinned : rest).push(...groupSection(g));
    } else if (!w.group) {
      (w.pinned ? pinned : rest).push(wsEntry(w, null));
    }
  }
  // Groups whose anchor never appeared (edge churn): append at the end.
  for (const g of groups.values()) {
    if (!seen.has(g.id) && ws.some((x) => x.group === g.id)) {
      seen.add(g.id);
      (g.pinned ? pinned : rest).push(...groupSection(g));
    }
  }
  return [...pinned, ...rest];
});

// --- drop resolution ---------------------------------------------------------
// `index` is the dragged row's slot in the flat list (headers included).
// `extra.side` resolves the ambiguous boundary slots: "above" nests with the
// row above (e.g. last item of a group), "below" with the row below (right
// after the group, outside it) - chosen by the pointer's X position mid-drag.
// Dragging a group HEADER moves the whole block (extra.block).
function handleMove(id, index, extra) {
  // Use the order currently rendered, including optimistic reorder overrides.
  // The host-provided `index` fields can lag behind that view for one or more
  // frames after a bulk or group move.
  const ws = visibleWorkspaces();

  if (extra && extra.block && id.startsWith("h:")) {
    // Whole-group move. workspace.group.move is NOT usable here: its
    // to_index is a group-slot index (position among groups, clamped to the
    // pin tier), so a tabs index overshoots to "last group" and a drop
    // between ungrouped rows is unreachable. Instead send the full tabs
    // order with the block extracted and re-inserted contiguously (anchor
    // first) at the drop slot - the app's contiguity normalization keeps it.
    const gid = id.slice(2);
    const memberIds = new Set(membersOf(gid).map((w) => w.id));
    const entries = flatEntries().filter((e) => e.id !== id && e.groupId !== gid);
    // The next entry that stays put anchors the drop. A header counts too:
    // dropping right above a (possibly collapsed) group means "before its
    // anchor", not "after its hidden members".
    const nextEntry = entries.slice(index).find((e) => e.kind === "ws" || e.kind === "header");
    const nextId = nextEntry
      ? (nextEntry.kind === "header" ? groupById(nextEntry.groupId)?.anchorId : nextEntry.wsId)
      : null;
    const anchorId = groupById(gid)?.anchorId;
    const blockIds = ws.map((x) => x.id).filter((x) => memberIds.has(x));
    if (anchorId && blockIds.includes(anchorId)) {
      blockIds.splice(blockIds.indexOf(anchorId), 1);
      blockIds.unshift(anchorId);
    }
    const rest = ws.map((x) => x.id).filter((x) => !memberIds.has(x));
    let insertAt = nextId ? rest.indexOf(nextId) : rest.length;
    if (insertAt < 0) insertAt = rest.length;
    const full = [...rest.slice(0, insertAt), ...blockIds, ...rest.slice(insertAt)];
    setOrderOverride(full); // paint the new order now; reorder_many echoes behind it
    cmux("workspace.reorder_many", { workspace_ids: JSON.stringify(full) });
    return;
  }

  const dragged = ws.find((w) => w.id === id);
  if (!dragged) return;

  // Dragging a row that is part of the multi-selection moves the WHOLE
  // selection: the visible selected rows gather contiguously at the drop
  // slot (visual order preserved) and all take the slot's container. This is
  // the platform-standard resolution for non-contiguous selections and for
  // selections mixing in-group and ungrouped rows. Hidden rows (inside a
  // collapsed group) never move - what you see is what you drag.
  multiTick();
  const bulk = multiSelected.has(id) && multiSelected.size > 1;
  const movingIds = bulk
    ? visibleRowIds().filter((rid) => multiSelected.has(rid) || rid === id)
    : [id];
  const moving = new Set(movingIds);

  const entries = flatEntries().filter((e) => e.id !== id);
  // Neighbors that will NOT move: rows moving with the drag can't define the
  // drop's container or anchor.
  let prev = null;
  for (let i = index - 1; i >= 0; i -= 1) {
    const e = entries[i];
    if (e.kind === "ws" && moving.has(e.wsId ?? e.id)) continue;
    prev = e;
    break;
  }
  const stays = (e) => !(e.kind === "ws" && moving.has(e.wsId ?? e.id));
  // The drop's tabs-order anchor is the next entry that stays put. A header
  // resolves to its group's ANCHOR workspace: dropping above a group means
  // "before the whole block", never "between its anchor and members" (which
  // would break contiguity and get normalized somewhere else).
  const nextEntry = entries.slice(index).find((e) => {
    if (e.kind === "header") return !moving.has(groupById(e.groupId)?.anchorId);
    return e.kind === "ws" && stays(e);
  });
  const nextAny = entries.slice(index).find(stays) ?? null;
  const nextRefId = nextEntry
    ? (nextEntry.kind === "header" ? groupById(nextEntry.groupId)?.anchorId : (nextEntry.wsId ?? nextEntry.id))
    : null;
  const nextWorkspace = nextRefId ? ws.find((w) => w.id === nextRefId) : null;

  let container;
  if (extra && extra.side === "below") {
    // Nest with what's below: a header below means "above the next group",
    // i.e. ungrouped; a row below means its group (or ungrouped).
    container = nextAny && nextAny.kind === "ws" ? nextAny.groupId : null;
  } else {
    container = prev ? prev.groupId : null;
    // Dropping right below a collapsed group's header means "after the whole
    // group", not "into it" (its rows are hidden), unless it lives there.
    if (prev && prev.kind === "header") {
      const g = groupById(prev.groupId);
      if (g && isCollapsed(g) && dragged.group !== g.id) container = null;
    }
  }

  for (const rid of movingIds) {
    const row = ws.find((w) => w.id === rid);
    if (!row) continue;
    if ((row.group ?? null) !== container) {
      if (container) {
        cmux("workspace.group.add", { group_id: container, workspace_id: rid });
      } else {
        cmux("workspace.group.remove", { workspace_id: rid });
      }
    }
  }

  if (bulk) {
    // Atomic block placement: send the full tabs order with the moving rows
    // inserted contiguously before the anchor.
    const rest = ws.map((x) => x.id).filter((x) => !moving.has(x));
    let insertAt = nextWorkspace ? rest.indexOf(nextWorkspace.id) : rest.length;
    if (insertAt < 0) insertAt = rest.length;
    const full = [...rest.slice(0, insertAt), ...movingIds, ...rest.slice(insertAt)];
    setOrderOverride(full); // gather instantly; reorder_many echoes behind it
    cmux("workspace.reorder_many", { workspace_ids: JSON.stringify(full) });
    clearMultiSelect();
    return;
  }

  if (nextWorkspace) {
    const draggedPosition = ws.findIndex((w) => w.id === dragged.id);
    const before = ws.findIndex((w) => w.id === nextWorkspace.id);
    const target = draggedPosition < before ? before - 1 : before;
    cmux("workspace.reorder", { workspace_id: id, index: target });
  } else {
    cmux("workspace.reorder", { workspace_id: id, index: ws.length - 1 });
  }
  // Dragging an unselected row with a selection active clears the stale
  // selection (platform convention).
  clearMultiSelect();
}

// --- rows ----------------------------------------------------------------------
function workspaceMenu(w) {
  const act = (action) => () =>
    cmux("workspace.action", { action, workspace_id: w().id });
  const groupItems = (data.groups() ?? []).map((g) =>
    Button(() => (groupById(g.id)?.name ?? ""), () => {
      for (const id of bulkIds(w())) cmux("workspace.group.add", { group_id: g.id, workspace_id: id });
      clearMultiSelect();
    }));
  const count = () => bulkIds(w()).length;
  return [
    Button(() => (count() > 1 ? "New Group from " + count() + " Workspaces" : "New Group with This"), () => {
      cmux("workspace.group.create", {
        name: "New Group",
        child_workspace_ids: JSON.stringify(bulkIds(w())),
      });
      clearMultiSelect();
    }),
    Divider(),
    Button("Rename", () => setEditingId(w().id)),
    Button(() => (w()?.pinned ? "Unpin" : "Pin"), () =>
      cmux("workspace.action", { action: w()?.pinned ? "unpin" : "pin", workspace_id: w().id })),
    Button(() => (w()?.unread > 0 ? "Mark as Read" : "Mark as Unread"), () =>
      cmux("workspace.action", { action: w()?.unread > 0 ? "mark_read" : "mark_unread", workspace_id: w().id })),
    Divider(),
    Menu("Move", [
      Button("Move Up", act("move_up")),
      Button("Move Down", act("move_down")),
      Button("Move to Top", act("move_top")),
    ]),
    Menu("Move to Group", groupItems),
    Button("Remove from Group", () => cmux("workspace.group.remove", { workspace_id: w().id })),
    Divider(),
    Button("Close Others", act("close_others")).destructive(),
    Button(() => (count() > 1 ? "Close " + count() + " Workspaces" : "Close"), () => {
      for (const id of bulkIds(w())) closeWorkspace(id);
      clearMultiSelect();
    }).destructive(),
  ];
}

const rowPreferences = sidebarConfig.preferences;
const sidebarIconSize = 12;

function sidebarIcon(symbol) {
  return Image(symbol).font(10)
    .frame({ width: sidebarIconSize, height: sidebarIconSize }).fixedSize();
}

const agentStyles = {
  working: { label: "Working", symbol: "circle.fill", color: "blue" },
  needs_input: { label: "Needs input", symbol: "circle.fill", color: "red" },
  finished: { label: "Finished", symbol: "checkmark.circle.fill", color: "green", finished: true },
  idle: { label: "Idle", symbol: "circle", color: "secondary" },
};

function agentStyle(agent, workspace) {
  // cmux reports completed turns as idle; only their unread surface needs attention.
  if (agent.status === "idle" && workspace?.tabs?.some(
    (tab) => tab.id === agent.panelId && tab.hasUnread
  )) return agentStyles.finished;
  return agentStyles[agent.status] ?? {
    label: agent.status, symbol: "circle.dashed", color: "secondary",
  };
}

function shortDirectory(path, remote) {
  if (!path) return "";
  if (rowPreferences.sidebarPathLastSegmentOnly) {
    return path.replace(/\/+$/, "").split("/").pop() || "/";
  }
  const home = sidebarConfig.homeDirectory.replace(/\/+$/, "");
  if (!remote && (path === home || path.startsWith(home + "/"))) {
    return "~" + path.slice(home.length);
  }
  return path;
}

function workspaceMetadata(workspace) {
  if (!workspace || rowPreferences.sidebarHideAllDetails) return [];
  const rows = [];
  const addText = (id, text, icon, options = {}) => {
    if (text) rows.push({ id, kind: "text", text: String(text).slice(0, 4096), icon, ...options });
  };
  if (rowPreferences.sidebarShowWorkspaceDescription) {
    addText("description", workspace.description?.trim(), null, {
      lines: 2, color: rowPreferences.sidebarWorkspaceDescriptionColorHex || "secondary",
    });
  }
  if (rowPreferences.sidebarShowNotificationMessage) {
    addText("notification", workspace.latestMessage?.trim(), "bubble.left", {
      lines: rowPreferences.sidebarNotificationMessageLineLimit,
    });
  }
  if (rowPreferences.sidebarShowStatusPills) {
    for (const agent of workspace.agents ?? []) {
      // Restored history can be idle without a process; it is not an open agent.
      if (agent.status === "ended" || !Number.isInteger(agent.pid) || agent.pid <= 0) continue;
      if (!workspace.tabs?.some((tab) => tab.id === agent.panelId)) continue;
      rows.push({ id: "agent:" + agent.id, kind: "agent", agent });
    }
  }
  if (rowPreferences.sidebarShowSSH && workspace.remote?.target) {
    addText("remote", workspace.remote.target + (workspace.remote.state ? " · " + workspace.remote.state : ""),
      "network");
  }
  if (rowPreferences.sidebarShowProgress && Number.isFinite(workspace.progress?.value)) {
    rows.push({ id: "progress", kind: "progress", value: Math.max(0, Math.min(1, workspace.progress.value)),
      label: workspace.progress.label || "" });
  }
  if (rowPreferences.sidebarShowBranchDirectory) {
    const vertical = rowPreferences.sidebarBranchVerticalLayout;
    const stacked = vertical || rowPreferences.sidebarBranchDirectoryStacked;
    const panels = vertical ? (workspace.tabs ?? []).filter((tab) => tab.directory || tab.branch) : [];
    const records = panels.length ? panels : [workspace];
    const seen = new Set();
    for (const [index, record] of records.entries()) {
      const sameDirectory = record.directory === workspace.directory;
      const branchName = record.branch || (sameDirectory ? workspace.branch : "");
      const dirty = record.branch ? record.dirty : sameDirectory && workspace.dirty;
      const branch = branchName ? branchName + (dirty ? " *" : "") : "";
      const directory = shortDirectory(record.directory, workspace.remote);
      const identity = JSON.stringify([branch, record.directory || ""]);
      if (seen.has(identity)) continue;
      seen.add(identity);
      if (stacked) {
        addText("branch:" + index, branch, "arrow.triangle.branch", { monospaced: true });
        addText("directory:" + index, directory, "folder", { help: record.directory });
      } else {
        addText("location:" + index, [branch, directory].filter(Boolean).join(" · "),
          branch ? "arrow.triangle.branch" : "folder",
          { help: [branch, record.directory].filter(Boolean).join(" · "), monospaced: true });
      }
    }
  }
  if (rowPreferences.sidebarShowPullRequest) {
    const prs = workspace.prs?.length ? workspace.prs : workspace.pr ? [workspace.pr] : [];
    for (const pr of prs) {
      addText("pr:" + pr.url, "#" + pr.number + " · " + pr.status,
        pr.status === "merged" ? "arrow.triangle.merge" : "arrow.triangle.pull",
        { help: [pr.label, pr.url].filter(Boolean).join("\n") });
    }
  }
  if (rowPreferences.sidebarShowPorts && workspace.ports?.length) {
    addText("ports", workspace.ports.join(", "), "network");
  }
  return rows;
}

function workspaceMetadataRows(w) {
  return ForEach(
    { items: () => workspaceMetadata(w()), key: (row) => row.id },
    (row) => {
      if (row().kind === "agent") {
        return HStack({ spacing: 4 }, [
          sidebarIcon(() => agentStyle(row().agent, w()).symbol)
            .color(() => agentStyle(row().agent, w()).color)
            .help(() => agentStyle(row().agent, w()).label),
          Text(() => {
            const style = agentStyle(row().agent, w());
            return (row().agent.name || row().agent.kind) + (style.finished ? " · Finished" : "");
          }).font(11)
            .color(() => agentStyle(row().agent, w()).finished ? "green" : "secondary")
            .weight(() => agentStyle(row().agent, w()).finished ? "semibold" : "regular")
            .lineLimit(1).truncation("tail"),
          Spacer({ minLength: 0 }),
        ]).help(() => (row().agent.name || row().agent.kind) + ": " + agentStyle(row().agent, w()).label);
      }
      if (row().kind === "progress") {
        return VStack({ alignment: "leading", spacing: 2 }, [
          ProgressView({ value: () => row().value }).frame({ maxWidth: "infinity" }),
          ForEach({ items: () => row().label ? [row().label] : [], key: () => "label" },
            (label) => Text(() => label()).font(10).color("secondary").lineLimit(1)),
        ]);
      }
      return HStack({ alignment: "top", spacing: 4 }, [
        ForEach({ items: () => row().icon ? [row().icon] : [], key: (icon) => icon },
          (icon) => sidebarIcon(() => icon()).color("secondary")),
        Text(() => row().text).font(12)
          .color(() => row().color || "secondary")
          .monospaced(() => !!row().monospaced)
          .lineLimit(() => row().lines || 1)
          .truncation(() => row().id.startsWith("directory:") ? "middle" : "tail")
          .fixedSize("vertical")
          .frame({ maxWidth: "infinity", alignment: "leading" }),
      ]).help(() => row().help || row().text);
    }
  );
}

function titleIndicators(w, side) {
  return ForEach({
    items: () => {
      const workspace = w();
      if (!workspace) return [];
      const indicators = [];
      const unreadHere = workspace.unread > 0 && rowPreferences.sidebarNotificationBadgePosition === side;
      if (unreadHere) indicators.push({ id: "unread", count: workspace.unread });
      if (!unreadHere && rowPreferences.sidebarShowAgentActivity
          && rowPreferences.sidebarLoadingSpinnerPosition === side
          && workspace.agents?.some((agent) => agent.status === "working")) {
        indicators.push({ id: "activity" });
      }
      if (side === "leading" && workspace.pinned) indicators.push({ id: "pin" });
      return indicators;
    },
    key: (indicator) => indicator.id,
  }, (indicator) => {
    if (indicator().id === "pin") return sidebarIcon("pin.fill").color("secondary");
    if (indicator().id === "activity") {
      return ProgressView().frame({ width: sidebarIconSize, height: sidebarIconSize }).help("Agent working");
    }
    // A separate sized shape avoids text-background/frame ordering in cmux.
    return ZStack({ alignment: "center" }, [
      RoundedRectangle().fill(rowPreferences.sidebarNotificationBadgeColorHex || "blue")
        .cornerRadius(3).frame({ width: sidebarIconSize, height: sidebarIconSize }),
      Text(() => indicator().count > 99 ? "99+" : String(indicator().count))
        .font(() => indicator().count > 99 ? 5.5 : 7).weight("semibold").color("white").fixedSize(),
    ]).frame({ width: sidebarIconSize, height: sidebarIconSize })
      .help(() => indicator().count + " unread notification" + (indicator().count === 1 ? "" : "s"));
  });
}

function workspaceTitleRow(w) {
  return HStack({ alignment: "top", spacing: 4 }, [
    // Center 12-point indicators on the title's first line, even when it wraps.
    titleIndicators(w, "leading").paddingTop(2),
    Text(() => displayTitle(w()).slice(0, 2048))
      .font(13).color("primary")
      .lineLimit(rowPreferences.sidebarWrapWorkspaceTitles ? 8 : 1).truncation("tail")
      .fixedSize("vertical")
      .frame({ maxWidth: "infinity", alignment: "leading" })
      .help(() => displayTitle(w())),
    titleIndicators(w, "trailing").paddingTop(2),
    ZStack({}, [sidebarIcon("xmark").color("secondary")]).padding(4)
      .cornerRadius(9).hoverBackground("#7f7f7f4a").showOnHover()
      .help("Close workspace").onTap(() => closeWorkspace(w().id)),
  ]);
}

function workspaceRow(w, entry) {
  return ZStack({ alignment: "leading" }, [
    Rectangle().fill(() => isSelected(w()) && rowPreferences.sidebarActiveTabIndicatorStyle === "leftRail"
      ? "accent" : "clear").frame({ width: 2, maxHeight: "infinity" }),
    VStack({ alignment: "leading", spacing: 4 }, [
      workspaceTitleRow(w),
      workspaceMetadataRows(w),
    ]).paddingHorizontal(10).paddingVertical(6),
  ])
    .marginLeading(() => (entry().groupId ? 14 : 0))
    .cornerRadius(8)
    .background(() => isMultiSelected(w()) ? "#4C9EEB33" :
      isSelected(w()) ? rowPreferences.sidebarSelectionColorHex || "#7f7f7f24" : null)
    .hoverBackground(() => isMultiSelected(w()) ? "#4C9EEB33" :
      isSelected(w()) ? rowPreferences.sidebarSelectionColorHex || "#7f7f7f24" : "#7f7f7f18")
    .frame({ maxWidth: "infinity" })
    .block(() => (entry().groupId ? "h:" + entry().groupId : null))
    .dragSet(() => (isMultiSelected(w()) ? "multi" : null))
    .onTap((payload) => handleRowClick(w(), payload))
    .onDoubleTap(() => setEditingId(w().id))
    .contextMenu(workspaceMenu(w));
}

// In-place editor row (same box as a workspace row).
function workspaceEditRow(w, entry) {
  return VStack({ alignment: "leading", spacing: 3 }, [
    TextField(() => w()?.title ?? "", {
      placeholder: "Workspace name",
      onSubmit: (t) => {
        const title = (t ?? "").trim();
        if (title) {
          titleOverride.set(w().id, title);
          setTitleTick(titleTick() + 1);
          cmux("workspace.action", { action: "rename", workspace_id: w().id, title });
        } else {
          cmux("workspace.action", { action: "clear_name", workspace_id: w().id });
        }
        setEditingId(null);
      },
      onCancel: () => setEditingId(null),
    }).font(13),
    workspaceMetadataRows(w),
  ])
    .paddingHorizontal(10)
    .paddingVertical(6)
    .cornerRadius(8)
    .background("#7f7f7f3d")
    .marginLeading(() => (entry().groupId ? 14 : 0))
    .frame({ maxWidth: "infinity" });
}

function groupHeader(groupId) {
  const g = () => groupById(groupId) ?? { id: groupId, name: "", collapsed: false, pinned: false };
  const anchor = () => (data.workspaces() ?? []).find((w) => w.id === g().anchorId);
  const groupAct = (action) => () =>
    cmux("workspace.group.action", { group_id: groupId, action });
  return HStack({ spacing: 6 }, [
    // The chevron toggles collapse; clicking anywhere else selects the
    // group's anchor workspace (built-in sidebar behavior). Chevron only,
    // no folder icon. One glyph that ROTATES (right -> down on expand):
    // rotation animates as one motion with the accordion, and the fixed box
    // keeps the header height constant.
    sidebarIcon("chevron.right").weight("semibold").color("tertiary")
      .rotation(() => (isCollapsed(g()) ? 0 : 90))
      .onTap(() => toggleCollapse(g())),
    Text(() => g().name).font(12).weight("semibold").lineLimit(1).truncation("tail")
      .color(() => (isSelected(anchor()) ? "primary" : "secondary")),
    Spacer(),
  ])
    .paddingLeading(8)
    .paddingTrailing(10)
    .paddingVertical(5)
    .cornerRadius(8)
    .background(() => (isSelected(anchor()) ? "#7f7f7f3d" : null))
    .hoverBackground(() => (isSelected(anchor()) ? "#7f7f7f3d" : "#7f7f7f1c"))
    .frame({ maxWidth: "infinity" })
    .fixed()
    .block("h:" + groupId)
    .onTap(() => selectWorkspace(anchor()?.id))
    .onDoubleTap(() => setEditingId("h:" + groupId))
    .contextMenu([
      Button("Rename Group", () => setEditingId("h:" + groupId)),
      Button(() => (isCollapsed(g()) ? "Expand" : "Collapse"), () => toggleCollapse(g())),
      Button(() => (g().pinned ? "Unpin Group" : "Pin Group"), () =>
        cmux("workspace.group.action", { group_id: groupId, action: g().pinned ? "unpin" : "pin" })),
      Divider(),
      Button("Ungroup", groupAct("ungroup")),
      Button("Delete Group", groupAct("delete")).destructive(),
    ]);
}

// Identical geometry to groupHeader (chevron box, paddings, semibold 12)
// so entering/leaving rename changes nothing but the text becoming editable.
function groupEditRow(groupId) {
  const g = () => groupById(groupId);
  return HStack({ spacing: 6 }, [
    sidebarIcon("chevron.right").weight("semibold").color("tertiary")
      .rotation(() => (isCollapsed(g() ?? {}) ? 0 : 90)),
    TextField(() => g()?.name ?? "", {
      placeholder: "Group name",
      onSubmit: (t) => {
        const name = (t ?? "").trim();
        if (name) cmux("workspace.group.rename", { group_id: groupId, name });
        setEditingId(null);
      },
      onCancel: () => setEditingId(null),
    }).font(12).weight("semibold"),
  ])
    .paddingLeading(8)
    .paddingTrailing(10)
    .paddingVertical(5)
    .cornerRadius(8)
    .background("#7f7f7f3d")
    .frame({ maxWidth: "infinity" })
    .fixed();
}

// --- independent external data -------------------------------------------------
// Only the clock-dependent freshness label runs on ticks. Flatten and bound the
// literal source strings once per generated script load; never execute their text.
const externalSummary = (() => {
  const sections = externalSnapshot.sections ?? [];
  const errors = [];
  const output = [];
  const literalLine = (value) => {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text.length > 220 ? text.slice(0, 220) + "… [truncated]" : text;
  };
  const title = sections.length === 1 ? literalLine(sections[0].title) || "Local data" : "Local data";
  for (const section of sections) {
    const prefix = sections.length > 1 ? literalLine(section.title) + ": " : "";
    if (section.error) errors.push(prefix + "Error: " + literalLine(section.error));
    for (const item of section.items ?? []) {
      output.push(literalLine(prefix + item.title + (item.detail ? " — " + item.detail : "")));
    }
    if (!section.error && !(section.items ?? []).length) output.push(prefix + "No items");
  }
  if (!sections.length && !errors.length) output.push("No sources configured");
  const bounded = (lines, label) => lines.length > 8
    ? [...lines.slice(0, 8), "… " + (lines.length - 8) + " more " + label + " omitted"]
    : lines;
  const full = [...bounded(errors, "errors"), ...bounded(output, "outputs")];
  const preview = errors.length
    ? [errors[0], ...(errors.length > 1 ? ["… " + (errors.length - 1) + " more errors — expand"] : []),
      ...output.slice(0, errors.length > 1 ? 1 : 2)]
    : output.slice(0, 3);
  const rows = (lines) => lines.map((text, id) => ({ id, text }));
  return {
    title,
    errorCount: errors.length,
    preview: rows(preview),
    full: rows(full),
    expandable: errors.length > 1 || full.length > preview.length,
    generatedEpoch: Date.parse(externalSnapshot.generatedAt) / 1000,
    refreshAfterSeconds: externalSnapshot.refreshAfterSeconds,
  };
})();
const [externalExpanded, setExternalExpanded] = signal(false);

function externalFreshness() {
  const now = data.clock()?.epoch ?? 0;
  const age = Math.max(0, now - externalSummary.generatedEpoch);
  const stale = age > externalSummary.refreshAfterSeconds;
  const freshness = !Number.isFinite(age) ? "Unknown age" : stale ? "Stale" : "Fresh";
  return freshness + (externalSummary.errorCount
    ? " · " + externalSummary.errorCount + (externalSummary.errorCount === 1 ? " error" : " errors") : "");
}

function externalDataRow() {
  return VStack({ spacing: 3, alignment: "leading" }, [
    HStack({ spacing: 6 }, [
      Text(externalSummary.title).font(12).weight("semibold")
        .lineLimit(1).truncation("tail").color("secondary"),
      Spacer({ minLength: 0 }),
      Text(externalFreshness).font(10)
        .color(() => externalSummary.errorCount || externalFreshness().startsWith("Stale") ? "#C18436" : "tertiary")
        .lineLimit(1),
      sidebarIcon("chevron.right").color("tertiary")
        .rotation(() => externalExpanded() ? 90 : 0)
        .opacity(externalSummary.expandable ? 1 : 0),
    ]),
    ForEach(
      { items: () => externalExpanded() ? externalSummary.full : externalSummary.preview, key: (line) => line.id },
      (line) => Text(() => line().text).font(11).color("secondary")
        .lineLimit(1).truncation("tail")
        .help(() => line().text)
        .frame({ maxWidth: "infinity", alignment: "leading" })
    ),
  ])
    .paddingHorizontal(10)
    .paddingVertical(6)
    .frame({ maxWidth: "infinity", alignment: "leading" })
    .background("#7f7f7f12")
    .cornerRadius(8)
    .onTap(() => {
      if (externalSummary.expandable) setExternalExpanded(!externalExpanded());
    });
}

// --- root ------------------------------------------------------------------------
sidebar(() =>
  VStack({ spacing: 4 }, [
  ...(externalPosition === "bottom" ? [] : [externalDataRow()]),
  Reorderable(
    {
      items: flatEntries,
      key: (e) => e.id,
      spacing: 2,
      onMove: handleMove,
    },
    (e, key) => {
      const entry = e(); // kind, ids, and editing are stable per key
      if (entry.kind === "header") {
        return entry.editing ? groupEditRow(entry.groupId) : groupHeader(entry.groupId);
      }
      const w = () => (data.workspaces() ?? []).find((x) => x.id === entry.wsId);
      return entry.editing ? workspaceEditRow(w, e) : workspaceRow(w, e);
    }
  ),
  ...(externalPosition === "bottom" ? [externalDataRow()] : []),
  ]),
  { surface: "glass" }
)
