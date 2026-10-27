# Evidence and quality

Assess factual support and explanatory adequacy separately. A sparse answer can be correct but insufficient; a detailed answer can connect true facts incorrectly.

## Preserve meaning and provenance

Use canonical references returned by the store: `[[SOURCE@REVISION:PASSAGE]]`. Retain title, origin, capture kind, completeness, and relevant edition or version. Revision identity establishes which capture was used, not its authority.

Use note kinds deliberately: `fact` for a supported assertion, `interpretation` for an attributed or qualified reading, `synthesis` for a connection with evidence and dependencies, and `question` for an unresolved issue. A speaker's belief, a narrator's account, an experimental measurement, and the researcher's inference are different claims.

Preserve distinctions that can change the answer: person, event phase, geography, population, date, units, method, speaker, edition, or software version. Adoption, publication, construction, and operation dates need not conflict. A city, province, and wider region are different populations even when a source uses the same place name.

If an accessible source quotes an unavailable original, cite the intermediary and identify indirect access. A snippet can support a narrowly stated detail but cannot establish full-text reading. Missing access is a limitation of the investigation; assert underlying uncertainty only when the examined evidence supports it.

## Check source origins

Evaluate the source for the particular claim: proximity, method, scope, date, and expertise. Primary sources can be mistaken; careful secondary work can supply needed interpretation.

Group copies, syndicated reports, shared press releases, and accounts derived from one study into the same `source_family` when known. Different domains do not establish independent corroboration. Unknown provenance remains unknown. Seek meaningful contrary evidence without manufacturing balance between unequal claims.

## Verify semantic support

For consequential factual, numerical, causal, or interpretive claims, reopen the cited passage and enough surrounding context. Check:

- Does it support this direction, quantity, identity, scope, and degree of certainty?
- Does it actually explain the proposed relationship, or merely mention its endpoints?
- Which part is the source's statement, and which part is the report's inference?
- Do different accounts concern the same period, place, edition, sample, method, and event?

Record the conclusion in the question's `support` judgment and short rationale, reusing the answer or `answer_note`. Do not copy entire sources into rationales. `context_read` means actual relevant context was inspected; neither ingestion nor `read-many` sets it automatically.

A valid reference, a number match, or an exact quotation is not proof of entailment. The helper cannot decide semantic support. A deliberately false claim with a genuine citation can pass structural checks; the reviewer must reject it.

For a real disagreement, preserve each position, its evidence and reasoning, and the evidence that could distinguish them. Explain its consequence for the answer. If only access or differing definitions explain the apparent conflict, say so rather than inventing an intellectual dispute. Corrected sources or claims require reconsidering dependent notes and explanations.

## Check explanatory coverage

Use preserved questions and source-derived candidates, as described in the [workflow](research-workflow.md#challenge-the-map-before-the-report-is-finished). A broad topic with one cited paragraph is not necessarily covered. Required child questions remain open even if their parent is marked covered.

Explanatory completeness depends on the user's request. A chronology may answer when something happened; it cannot by itself explain why it happened or how it changed later conditions. Look for the mechanism, intervening conditions, consequences, and significant alternatives. Preserve an explanatory gap when the evidence does not support more.

Before marking a question covered, establish that evidence was found, relevant context was read, the answer is supported, and the answer appears in the report. Use a specific report phrase for `report_anchor`, not a broad heading. These are declared judgments backed by records, not machine-certified understanding.

## Probe unfamiliar questions separately

For substantial studies, an examiner can prepare source-grounded probes without seeing the report, notes, or map: minor detail, a cross-section relationship, an alternative interpretation, a version difference, a false premise, or genuinely absent evidence. The investigator's post-draft checklist is self-review even if the schema calls its review `blind_questions`.

For memory evaluation, freeze the study first and use a fresh answering context with previously undisclosed questions. Distinguish answers recovered from report/notes, reopened stored passages or raw files, and new internet research. Give compared systems equal retained-material access. Memory performance is a separate result; do not add it to report coverage again.

Diagnose failures as discovery, capture, reading, retrieval, reasoning, or report-transfer problems. Recheck the relevant representation instead of memorizing a failed probe's answer. Small model-reviewed samples do not establish universal mastery, an accuracy percentage, or superiority.

## Review and outcome

Finalize the report before attesting `scope`, `citations`, and `blind_questions`. Identify the actual reviewer and method (`independent-agent`, `human`, or `self`) and record concrete findings. Sealed candidates or a different role name do not establish an independent context. The helper binds reviews to report and research hashes; changed content requires renewed checking.

Use `complete-within-scope` only when necessary reading, central and requested answers, explanatory adequacy, and required checks support it. An accurately explained open interpretation may remain; an unfilled central requirement may not. For an open topic, not reading all possible literature is not itself failure.

Use `partial` for missing central evidence, unsupported consequential claims, incomplete required checks, or resource stops. Distinguish inaccessible evidence, insufficient evidence, genuine disagreement, and deliberate scope exclusions. Mechanical verification establishes record integrity, never factual truth or a quality score.
