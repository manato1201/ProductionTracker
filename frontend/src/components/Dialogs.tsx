import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, FormControlLabel, MenuItem, TextField } from "@mui/material";
import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { entities, projects, tasks, versions } from "../api/endpoints";
import type { Entity, Member, Priority, Project, Step, Task } from "../api/types";
import { PRIORITIES, PRIORITY_META } from "../domain/status";
import { FormDialog } from "./FormDialog";

const dateProps = { type: "date", InputLabelProps: { shrink: true } } as const;

export function ProjectFormDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (p: Project) => void }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [start, setStart] = useState("");
  const [due, setDue] = useState("");
  return (
    <FormDialog
      open={open}
      title="プロジェクトを作成"
      submitLabel="作成"
      onClose={onClose}
      onSubmit={async () => {
        const created = await projects.create({ code, name, start: start || null, due: due || null });
        setCode("");
        setName("");
        setStart("");
        setDue("");
        onCreated(created);
      }}
    >
      <TextField label="コード" required value={code} onChange={(e) => setCode(e.target.value)} helperText="英字で始まる英数字・_・-(URL に使います。作成後は変更できません)" inputProps={{ maxLength: 32 }} />
      <TextField label="名前" required value={name} onChange={(e) => setName(e.target.value)} inputProps={{ maxLength: 120 }} />
      <TextField label="開始日" value={start} onChange={(e) => setStart(e.target.value)} {...dateProps} />
      <TextField label="期日" value={due} onChange={(e) => setDue(e.target.value)} {...dateProps} />
    </FormDialog>
  );
}

export function EntityFormDialog({ open, project, onClose, onCreated }: { open: boolean; project: Project; onClose: () => void; onCreated: (e: Entity) => void }) {
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  return (
    <FormDialog
      open={open}
      title="アセットを追加"
      submitLabel="追加"
      onClose={onClose}
      onSubmit={async () => {
        onCreated(await entities.create({ project: project.id, name, path }));
        setName("");
        setPath("");
      }}
    >
      <TextField label="名前" required value={name} onChange={(e) => setName(e.target.value)} inputProps={{ maxLength: 120 }} />
      <TextField label="パス" value={path} onChange={(e) => setPath(e.target.value)} helperText="品質スキャンの結果との突き合わせに使います(前方一致。例: assets/props/crate)" />
    </FormDialog>
  );
}

export function TaskFormDialog({
  open, entities: entityList, defaultEntityId, usedStepIds, steps, members, onClose, onCreated,
}: {
  open: boolean;
  entities: Entity[];
  defaultEntityId?: number;
  /** アセットごとに作成済みの工程(同じ工程は 1 アセットに 1 つ) */
  usedStepIds: (entityId: number) => number[];
  steps: Step[];
  members: Member[];
  onClose: () => void;
  onCreated: (t: Task) => void;
}) {
  const [entityId, setEntityId] = useState<number | "">("");
  const [step, setStep] = useState<number | "">("");
  const [assignee, setAssignee] = useState<number | "">("");
  const [due, setDue] = useState("");
  const [priority, setPriority] = useState<Priority>("normal");
  const [estimate, setEstimate] = useState("");
  const available = entityId === "" ? [] : steps.filter((s) => !usedStepIds(entityId).includes(s.id));

  useEffect(() => {
    if (open) setEntityId(defaultEntityId ?? entityList[0]?.id ?? "");
    // 意図: 開いたときだけ初期値を入れる(entityList などが変わるたびに入力中の値を上書きしない)
  }, [open]);
  useEffect(() => {
    setStep(available[0]?.id ?? "");
    // 意図: アセットを選び直した・開いた・工程が読み込まれたときだけ、工程の初期値を選び直す
  }, [entityId, open, steps.length]);

  return (
    <FormDialog
      open={open}
      title="タスクを追加"
      submitLabel="追加"
      onClose={onClose}
      onSubmit={async () => {
        if (entityId === "" || step === "") throw new ApiError(0, "invalid", "アセットと工程を選んでください。");
        onCreated(
          await tasks.create({
            entity: entityId,
            step,
            assignee: assignee === "" ? null : assignee,
            due: due || null,
            priority,
            estimate_h: estimate === "" ? null : Number(estimate),
          }),
        );
      }}
    >
      <TextField select label="アセット" required value={entityId} onChange={(e) => setEntityId(Number(e.target.value))}>
        {entityList.map((e) => (
          <MenuItem key={e.id} value={e.id}>{e.name}</MenuItem>
        ))}
      </TextField>
      {entityId !== "" && available.length === 0 ? <Alert severity="info">このアセットは、全ての工程のタスクが作成済みです。</Alert> : null}
      <TextField select label="工程" required value={step} onChange={(e) => setStep(Number(e.target.value))}>
        {available.map((s) => (
          <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
        ))}
      </TextField>
      <TextField select label="担当者" value={assignee} onChange={(e) => setAssignee(e.target.value === "" ? "" : Number(e.target.value))}>
        <MenuItem value="">未割当</MenuItem>
        {members.map((m) => (
          <MenuItem key={m.user} value={m.user}>{m.display_name}({m.role_label})</MenuItem>
        ))}
      </TextField>
      <TextField select label="優先度" value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
        {PRIORITIES.map((p) => (
          <MenuItem key={p} value={p}>{PRIORITY_META[p].label}</MenuItem>
        ))}
      </TextField>
      <TextField label="期日" value={due} onChange={(e) => setDue(e.target.value)} {...dateProps} />
      <TextField label="見積(時間)" type="number" value={estimate} onChange={(e) => setEstimate(e.target.value)} inputProps={{ min: 0, step: 0.5 }} />
    </FormDialog>
  );
}

export function VersionFormDialog({ open, task, onClose, onCreated }: { open: boolean; task: Task; onClose: () => void; onCreated: () => void }) {
  const [fileRef, setFileRef] = useState("");
  const [comment, setComment] = useState("");
  const [thumbnail, setThumbnail] = useState("");
  const [submitNow, setSubmitNow] = useState(true);
  return (
    <FormDialog
      open={open}
      title={`版を登録: ${task.entity_name} / ${task.step_name}`}
      submitLabel="登録"
      onClose={onClose}
      onSubmit={async () => {
        await versions.create({ task: task.id, file_ref: fileRef, comment, thumbnail, status: submitNow ? "submitted" : "draft" });
        setFileRef("");
        setComment("");
        setThumbnail("");
        onCreated();
      }}
    >
      <TextField label="ファイルの場所" required value={fileRef} onChange={(e) => setFileRef(e.target.value)} helperText="パスまたは URL" />
      <TextField label="サムネイル(画像の場所)" value={thumbnail} onChange={(e) => setThumbnail(e.target.value)} helperText="登録済みの画像の URL。変換・配信はしません" />
      <TextField label="コメント" multiline minRows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
      <FormControlLabel control={<Checkbox checked={submitNow} onChange={(e) => setSubmitNow(e.target.checked)} />} label="提出済みとして登録する" />
    </FormDialog>
  );
}

/** 「完了」にする前の確認(モーダル 01)。版が無い場合は警告する。 */
export function ConfirmDoneDialog({ task, onCancel, onConfirm }: { task: Task | null; onCancel: () => void; onConfirm: () => void }) {
  return (
    <Dialog open={task !== null} onClose={onCancel}>
      <DialogTitle>「完了」にしますか?</DialogTitle>
      <DialogContent>
        {task ? (
          <>
            <DialogContentText>
              {task.entity_name} / {task.step_name} を完了にします。承認できるのはレビュアーのみです。
            </DialogContentText>
            {task.version_count === 0 ? (
              <Alert severity="warning" sx={{ mt: 2 }}>
                このタスクには版がありません。版が無いと、完了にできない設定の場合は拒否されます。
              </Alert>
            ) : null}
          </>
        ) : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>キャンセル</Button>
        <Button variant="contained" onClick={onConfirm} autoFocus>
          完了にする
        </Button>
      </DialogActions>
    </Dialog>
  );
}
