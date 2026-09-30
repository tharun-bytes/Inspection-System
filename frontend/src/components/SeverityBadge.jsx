const LABELS = {
  minor: "Minor",
  major: "Major",
  critical: "Critical",
  pending: "Pending",
  passed: "Passed",
  failed: "Failed",
  review: "Needs review",
};

const TONE_CLASS = {
  minor: "badge badge--minor",
  major: "badge badge--major",
  critical: "badge badge--critical",
  pending: "badge badge--pending",
  passed: "badge badge--passed",
  failed: "badge badge--failed",
  review: "badge badge--review",
};

export function labelFor(value) {
  if (!value) return "Unscored";
  return LABELS[value] || value;
}

export default function SeverityBadge({ value }) {
  const tone = TONE_CLASS[value] || "badge badge--pending";
  return <span className={tone}>{labelFor(value)}</span>;
}
