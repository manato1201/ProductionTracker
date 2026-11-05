import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import { useBoardFilters } from "./useBoardFilters";

function Probe() {
  const [filters, setFilters, reset] = useBoardFilters();
  const location = useLocation();
  return (
    <>
      <output aria-label="url">{location.search}</output>
      <output aria-label="assignee">{filters.assignee}</output>
      <button onClick={() => setFilters({ assignee: "me" })}>自分</button>
      <button onClick={() => setFilters({ q: "crate" })}>検索</button>
      <button onClick={reset}>リセット</button>
    </>
  );
}

describe("useBoardFilters", () => {
  it("URL の値から始まり、変更は URL に反映される。task は残る", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/board?task=7&assignee=none"]}><Probe /></MemoryRouter>);
    expect(screen.getByLabelText("assignee")).toHaveTextContent("none");

    await user.click(screen.getByText("自分"));
    await user.click(screen.getByText("検索"));
    expect(screen.getByLabelText("url")).toHaveTextContent("?task=7&assignee=me&q=crate");

    await user.click(screen.getByText("リセット"));
    expect(screen.getByLabelText("url")).toHaveTextContent("?task=7");
    expect(screen.getByLabelText("assignee")).toHaveTextContent("all");
  });
});
