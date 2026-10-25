import { Chip } from "@mui/material";

interface Props {
  label: string;
  pressed: boolean;
  onClick: () => void;
  size?: "small" | "medium";
}

/** 絞り込み・並べ替えのチップ(13)。押下状態は色だけでなく `aria-pressed` でも伝える。 */
export function FilterChip({ label, pressed, onClick, size = "small" }: Props) {
  return (
    <Chip
      label={label}
      size={size}
      clickable
      aria-pressed={pressed}
      color={pressed ? "primary" : "default"}
      variant={pressed ? "filled" : "outlined"}
      onClick={onClick}
    />
  );
}
