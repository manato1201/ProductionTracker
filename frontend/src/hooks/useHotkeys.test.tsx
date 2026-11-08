import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { isTypingTarget, useHotkeys } from "./useHotkeys";

function Probe({ onJ, enabled = true }: { onJ: () => void; enabled?: boolean }) {
  useHotkeys({ j: onJ }, enabled);
  return <input aria-label="検索" />;
}

describe("useHotkeys", () => {
  it("キーを押すとハンドラが呼ばれる", async () => {
    const onJ = vi.fn();
    render(<Probe onJ={onJ} />);
    await userEvent.keyboard("j");
    expect(onJ).toHaveBeenCalledTimes(1);
  });

  it("入力欄の中では無効", async () => {
    const onJ = vi.fn();
    const { getByLabelText } = render(<Probe onJ={onJ} />);
    await userEvent.click(getByLabelText("検索"));
    await userEvent.keyboard("j");
    expect(onJ).not.toHaveBeenCalled();
  });

  it("修飾キー付き・無効時・ダイアログ表示中は無視する", async () => {
    const onJ = vi.fn();
    const { rerender } = render(<Probe onJ={onJ} />);
    await userEvent.keyboard("{Control>}j{/Control}");
    expect(onJ).not.toHaveBeenCalled();
    rerender(<Probe onJ={onJ} enabled={false} />);
    await userEvent.keyboard("j");
    expect(onJ).not.toHaveBeenCalled();
    rerender(<Probe onJ={onJ} />);
    const dlg = document.createElement("div");
    dlg.setAttribute("role", "dialog");
    document.body.append(dlg);
    await userEvent.keyboard("j");
    expect(onJ).not.toHaveBeenCalled();
    dlg.remove();
  });

  it("isTypingTarget", () => {
    expect(isTypingTarget(document.createElement("textarea"))).toBe(true);
    expect(isTypingTarget(document.createElement("button"))).toBe(false);
    expect(isTypingTarget(null)).toBe(false);
  });
});
