import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Button, IconButton, ListItemIcon, ListItemText, Menu, MenuItem } from "@mui/material";
import { useState, type MouseEvent } from "react";
import type { Task, TaskStatus } from "../api/types";
import { TASK_STATUS_META } from "../domain/status";

interface Props {
  task: Task;
  onSelect: (to: TaskStatus) => void;
  disabled?: boolean;
  variant: "icon" | "button";
}

/** 「状態を変更」メニュー。ドラッグに頼らない(キーボード・タッチ向け)の代替操作。 */
export function StatusMenu({ task, onSelect, disabled, variant }: Props) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const open = (e: MouseEvent<HTMLElement>) => {
    e.stopPropagation();
    setAnchor(e.currentTarget);
  };
  const label = `状態を変更: ${task.entity_name} / ${task.step_name}`;
  return (
    <>
      {variant === "icon" ? (
        <IconButton size="small" aria-label={label} aria-haspopup="menu" onClick={open} disabled={disabled} onMouseDown={(e) => e.stopPropagation()} onTouchStart={(e) => e.stopPropagation()}>
          <MoreVertIcon fontSize="small" />
        </IconButton>
      ) : (
        <Button size="small" variant="outlined" aria-haspopup="menu" onClick={open} disabled={disabled}>
          状態を変更
        </Button>
      )}
      {/* ドラッグの開始(dnd-kit は mousedown / touchstart を見る)をメニューのボタンで起こさない */}
      <Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)} onClick={(e) => e.stopPropagation()}>
        {task.next_statuses.length === 0 ? <MenuItem disabled>変更できる状態はありません</MenuItem> : null}
        {task.next_statuses.map((s) => {
          const { label: text, Icon } = TASK_STATUS_META[s];
          return (
            <MenuItem
              key={s}
              onClick={() => {
                setAnchor(null);
                onSelect(s);
              }}
            >
              <ListItemIcon><Icon fontSize="small" /></ListItemIcon>
              <ListItemText>{text}にする</ListItemText>
            </MenuItem>
          );
        })}
      </Menu>
    </>
  );
}
