import AssignmentIndOutlinedIcon from "@mui/icons-material/AssignmentIndOutlined";
import BrightnessAutoIcon from "@mui/icons-material/BrightnessAuto";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import FolderOutlinedIcon from "@mui/icons-material/FolderOutlined";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import { AppBar, Badge, Box, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, ListSubheader, Toolbar, Tooltip, useMediaQuery } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { get } from "../api/client";
import type { Page, Task } from "../api/types";
import { useAuth } from "../context/Auth";
import { useThemeMode } from "../context/ThemeMode";
import { useResource } from "../hooks/useResource";

const NAV_WIDTH = 232;

const THEME_ICON = { system: BrightnessAutoIcon, light: LightModeIcon, dark: DarkModeIcon } as const;
const THEME_LABEL = { system: "テーマ: OS の設定に合わせる", light: "テーマ: ライト", dark: "テーマ: ダーク" } as const;

function NavItem({ to, icon, label, badge, end, onClick }: { to: string; icon: React.ReactNode; label: string; badge?: number; end?: boolean; onClick?: () => void }) {
  const location = useLocation();
  const target = new URL(to, "http://x");
  const active = end
    ? location.pathname === target.pathname && location.search === target.search
    : location.pathname.startsWith(target.pathname) && (!target.search || location.search === target.search);
  return (
    <ListItemButton component={NavLink} to={to} selected={active} onClick={onClick} aria-current={active ? "page" : undefined}>
      <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>
      <ListItemText primary={label} />
      {badge ? (
        <Badge badgeContent={badge} color="error" max={99} sx={{ mr: 1 }} aria-label={`期限切れ ${badge} 件`} />
      ) : null}
    </ListItemButton>
  );
}

export function AppLayout() {
  const theme = useTheme();
  const wide = useMediaQuery(theme.breakpoints.up("md"));
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const mode = useThemeMode();
  const location = useLocation();
  const ModeIcon = THEME_ICON[mode.setting];

  // 自分の期限切れ件数(バッジ 23)。画面を移動するたびに更新する。
  const overdue = useResource(
    async () => (await get<Page<Task>>("/tasks/", { assignee: "me", overdue: 1, page_size: 1 })).count,
    [location.pathname],
  );

  const close = () => setOpen(false);
  const nav = (
    <List component="nav" aria-label="メインメニュー" sx={{ pt: 1 }}>
      <NavItem to="/me/tasks" end icon={<AssignmentIndOutlinedIcon />} label="自分のタスク" badge={overdue.data} onClick={close} />
      <NavItem to="/projects" icon={<FolderOutlinedIcon />} label="プロジェクト" onClick={close} />
      <ListSubheader sx={{ background: "transparent", lineHeight: "32px", mt: 1 }}>ビュー</ListSubheader>
      <NavItem to="/me/tasks?view=overdue" end icon={<ErrorOutlineIcon />} label="期限切れ" onClick={close} />
      <NavItem to="/me/tasks?view=review" end icon={<HourglassTopIcon />} label="レビュー待ち" onClick={close} />
    </List>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar position="fixed" color="inherit" elevation={0} sx={{ zIndex: (t) => t.zIndex.drawer + 1, borderBottom: 1, borderColor: "divider" }}>
        <Toolbar sx={{ gap: 1 }}>
          {!wide ? (
            <IconButton edge="start" aria-label="メニューを開く" onClick={() => setOpen(true)}><MenuIcon /></IconButton>
          ) : null}
          <Box component="strong" sx={{ flexGrow: 1, whiteSpace: "nowrap" }}>ProductionTracker</Box>
          <Tooltip title={THEME_LABEL[mode.setting]}>
            <IconButton aria-label={THEME_LABEL[mode.setting]} onClick={mode.cycle}><ModeIcon /></IconButton>
          </Tooltip>
          <Tooltip title={`${user?.display_name ?? ""} としてログイン中`}>
            <IconButton aria-label="ログアウト" onClick={() => void logout()}><LogoutIcon /></IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Drawer
        variant={wide ? "permanent" : "temporary"}
        open={wide || open}
        onClose={close}
        ModalProps={{ keepMounted: true }}
        sx={{ width: wide ? NAV_WIDTH : 0, flexShrink: 0, "& .MuiDrawer-paper": { width: NAV_WIDTH, boxSizing: "border-box" } }}
      >
        <Toolbar />
        {nav}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, minWidth: 0, p: { xs: 2, md: 3 } }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
