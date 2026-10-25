import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { formatDate } from "../domain/format";

/** 期日は等幅。期限切れは記号 + 文字でも示す。 */
export function DueText({ due, overdue }: { due: string | null; overdue: boolean }) {
  if (!due) return <span className="muted">期日なし</span>;
  if (overdue) {
    return (
      <span className="overdue">
        <ErrorOutlineIcon fontSize="small" aria-hidden />
        期限切れ <span className="num">{formatDate(due)}</span>
      </span>
    );
  }
  return (
    <span className="muted">
      期日 <span className="num">{formatDate(due)}</span>
    </span>
  );
}
