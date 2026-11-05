import { act, render, screen } from "@testing-library/react";
import { AsciiPlant } from "./AsciiPlant";
import { FRAME_INTERVAL_MS, GROWTH_FRAMES } from "../domain/motif";

function mockReducedMotion(reduce: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: reduce && query.includes("reduce"),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  })) as unknown as typeof window.matchMedia;
}

const text = () => screen.getByTestId("ascii-plant").textContent;

describe("AsciiPlant", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    // @ts-expect-error テストごとに matchMedia を元(無し)に戻す
    delete window.matchMedia;
  });

  it("飾りなので読み上げ対象にしない", () => {
    mockReducedMotion(false);
    render(<AsciiPlant status="todo" />);
    expect(screen.getByTestId("ascii-plant")).toHaveAttribute("aria-hidden", "true");
  });

  it("状態ごとに段階(種・芽・花・実)の絵を出し、既存の状態トークンの色クラスを使う", () => {
    mockReducedMotion(false);
    const { rerender } = render(<AsciiPlant status="todo" />);
    expect(text()).toBe(GROWTH_FRAMES.seed[0].join("\n"));
    expect(screen.getByTestId("ascii-plant")).toHaveClass("ascii-motif--todo");
    rerender(<AsciiPlant status="done" />);
    expect(text()).toBe(GROWTH_FRAMES.fruit[0].join("\n"));
    expect(screen.getByTestId("ascii-plant")).toHaveClass("ascii-motif--done");
  });

  it("動きを減らす設定では、静止画 1 枚のまま動かない", () => {
    mockReducedMotion(true);
    render(<AsciiPlant status="in_progress" />);
    const first = text();
    act(() => void vi.advanceTimersByTime(FRAME_INTERVAL_MS * 5));
    expect(text()).toBe(first);
    expect(first).toBe(GROWTH_FRAMES.sprout[0].join("\n"));
  });

  it("通常は一定間隔でコマが切り替わり、アンマウントで止まる", () => {
    mockReducedMotion(false);
    const { unmount } = render(<AsciiPlant status="in_progress" />);
    const first = text();
    act(() => void vi.advanceTimersByTime(FRAME_INTERVAL_MS));
    expect(text()).toBe(GROWTH_FRAMES.sprout[1].join("\n"));
    act(() => void vi.advanceTimersByTime(FRAME_INTERVAL_MS));
    expect(text()).toBe(first);
    unmount();
    expect(vi.getTimerCount()).toBe(0); // タイマーが残らない
  });

  it("タブが隠れている間は動かさない", () => {
    mockReducedMotion(false);
    render(<AsciiPlant status="review" />);
    const first = text();
    Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
    act(() => void vi.advanceTimersByTime(FRAME_INTERVAL_MS * 3));
    expect(text()).toBe(first);
    Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
  });
});
