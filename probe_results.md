# Probe results
## claude_ai (data/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv)
- Total row count: 1636573
- Distinct category_name: ['onet', 'overall', 'request', 'soc_occupation']
- Distinct geo_level: ['country', 'global', 'subregion']
- Distinct hierarchy_level: ['0', '1', '2', '3']
- Distinct date_start: ['2026-04-01', '2026-05-01']
- Distinct metric_id count: 53
- Full sorted metric_id list:
  - ai_autonomy_mean
  - ai_education_years_mean
  - artifact_academic_paper_or_thesis_pct
  - artifact_advice_or_recommendation_pct
  - artifact_analysis_or_summary_pct
  - artifact_app_or_website_pct
  - artifact_audio_or_music_pct
  - artifact_blog_or_article_pct
  - artifact_chart_or_visualization_pct
  - artifact_code_fix_or_debug_pct
  - artifact_config_or_infra_pct
  - artifact_creative_writing_pct
  - artifact_data_or_spreadsheet_pct
  - artifact_document_or_report_pct
  - artifact_educational_material_pct
  - artifact_email_or_message_pct
  - artifact_explanation_or_answer_pct
  - artifact_game_or_interactive_pct
  - artifact_idea_or_brainstorm_pct
  - artifact_image_or_graphic_pct
  - artifact_marketing_or_social_content_pct
  - artifact_math_or_calculation_pct
  - artifact_ml_or_ai_system_pct
  - artifact_none_pct
  - artifact_other_pct
  - artifact_plan_or_strategy_pct
  - artifact_presentation_or_slides_pct
  - artifact_recipe_or_meal_plan_pct
  - artifact_resume_or_job_application_pct
  - artifact_script_or_snippet_pct
  - artifact_sql_or_database_query_pct
  - artifact_translation_pct
  - artifact_ui_or_design_mockup_pct
  - artifact_video_or_animation_pct
  - collaboration_bucket_augmentation_pct
  - collaboration_bucket_automation_pct
  - collaboration_directive_pct
  - collaboration_feedback_loop_pct
  - collaboration_learning_pct
  - collaboration_none_pct
  - collaboration_task_iteration_pct
  - collaboration_validation_pct
  - human_education_years_mean
  - human_only_ability_pct
  - human_only_time_mean
  - human_with_ai_time_mean
  - multitasking_pct
  - pct
  - usage_pct
  - usage_per_capita_index
  - use_case_coursework_pct
  - use_case_personal_pct
  - use_case_work_pct
- Target slice (soc_occupation, hierarchy_level=0, geo_id=GLOBAL) row count: 72107
- Distinct node_name in slice: 718
- Ten sample node_external_id values: ['49-3092.00', '39-3012.00', '29-1122.00', '51-4081.00', '25-1082.00', '17-2121.00', '39-9032.00', '13-1071.00', '17-3026.01', '19-2012.00']
- Sample occupation for per-date metric listing: Accountants and Auditors
  - 2026-04-01: ['ai_autonomy_mean', 'ai_education_years_mean', 'artifact_academic_paper_or_thesis_pct', 'artifact_advice_or_recommendation_pct', 'artifact_analysis_or_summary_pct', 'artifact_app_or_website_pct', 'artifact_audio_or_music_pct', 'artifact_blog_or_article_pct', 'artifact_chart_or_visualization_pct', 'artifact_code_fix_or_debug_pct', 'artifact_config_or_infra_pct', 'artifact_creative_writing_pct', 'artifact_data_or_spreadsheet_pct', 'artifact_document_or_report_pct', 'artifact_educational_material_pct', 'artifact_email_or_message_pct', 'artifact_explanation_or_answer_pct', 'artifact_game_or_interactive_pct', 'artifact_idea_or_brainstorm_pct', 'artifact_image_or_graphic_pct', 'artifact_marketing_or_social_content_pct', 'artifact_math_or_calculation_pct', 'artifact_ml_or_ai_system_pct', 'artifact_none_pct', 'artifact_other_pct', 'artifact_plan_or_strategy_pct', 'artifact_presentation_or_slides_pct', 'artifact_recipe_or_meal_plan_pct', 'artifact_resume_or_job_application_pct', 'artifact_script_or_snippet_pct', 'artifact_sql_or_database_query_pct', 'artifact_translation_pct', 'artifact_ui_or_design_mockup_pct', 'artifact_video_or_animation_pct', 'collaboration_bucket_augmentation_pct', 'collaboration_bucket_automation_pct', 'collaboration_directive_pct', 'collaboration_feedback_loop_pct', 'collaboration_learning_pct', 'collaboration_none_pct', 'collaboration_task_iteration_pct', 'collaboration_validation_pct', 'human_education_years_mean', 'human_only_ability_pct', 'human_only_time_mean', 'human_with_ai_time_mean', 'multitasking_pct', 'pct', 'use_case_coursework_pct', 'use_case_personal_pct', 'use_case_work_pct']
  - 2026-05-01: ['ai_autonomy_mean', 'ai_education_years_mean', 'artifact_academic_paper_or_thesis_pct', 'artifact_advice_or_recommendation_pct', 'artifact_analysis_or_summary_pct', 'artifact_app_or_website_pct', 'artifact_audio_or_music_pct', 'artifact_blog_or_article_pct', 'artifact_chart_or_visualization_pct', 'artifact_code_fix_or_debug_pct', 'artifact_config_or_infra_pct', 'artifact_creative_writing_pct', 'artifact_data_or_spreadsheet_pct', 'artifact_document_or_report_pct', 'artifact_educational_material_pct', 'artifact_email_or_message_pct', 'artifact_explanation_or_answer_pct', 'artifact_game_or_interactive_pct', 'artifact_idea_or_brainstorm_pct', 'artifact_image_or_graphic_pct', 'artifact_marketing_or_social_content_pct', 'artifact_math_or_calculation_pct', 'artifact_ml_or_ai_system_pct', 'artifact_none_pct', 'artifact_other_pct', 'artifact_plan_or_strategy_pct', 'artifact_presentation_or_slides_pct', 'artifact_recipe_or_meal_plan_pct', 'artifact_resume_or_job_application_pct', 'artifact_script_or_snippet_pct', 'artifact_sql_or_database_query_pct', 'artifact_translation_pct', 'artifact_ui_or_design_mockup_pct', 'artifact_video_or_animation_pct', 'collaboration_bucket_augmentation_pct', 'collaboration_bucket_automation_pct', 'collaboration_directive_pct', 'collaboration_feedback_loop_pct', 'collaboration_learning_pct', 'collaboration_none_pct', 'collaboration_task_iteration_pct', 'collaboration_validation_pct', 'human_education_years_mean', 'human_only_ability_pct', 'human_only_time_mean', 'human_with_ai_time_mean', 'multitasking_pct', 'pct', 'use_case_coursework_pct', 'use_case_personal_pct', 'use_case_work_pct']

## 1p_api (data/release_2026_06_26/data/aei_1p_api_2026-06-26.csv)
- Total row count: 491705
- Distinct category_name: ['onet', 'overall', 'request', 'soc_occupation']
- Distinct geo_level: ['global']
- Distinct hierarchy_level: ['0', '1', '2', '3']
- Distinct date_start: ['2026-04-01', '2026-05-01']
- Distinct metric_id count: 53
- Full sorted metric_id list:
  - ai_autonomy_mean
  - ai_education_years_mean
  - artifact_academic_paper_or_thesis_pct
  - artifact_advice_or_recommendation_pct
  - artifact_analysis_or_summary_pct
  - artifact_app_or_website_pct
  - artifact_audio_or_music_pct
  - artifact_blog_or_article_pct
  - artifact_chart_or_visualization_pct
  - artifact_code_fix_or_debug_pct
  - artifact_config_or_infra_pct
  - artifact_creative_writing_pct
  - artifact_data_or_spreadsheet_pct
  - artifact_document_or_report_pct
  - artifact_educational_material_pct
  - artifact_email_or_message_pct
  - artifact_explanation_or_answer_pct
  - artifact_game_or_interactive_pct
  - artifact_idea_or_brainstorm_pct
  - artifact_image_or_graphic_pct
  - artifact_marketing_or_social_content_pct
  - artifact_math_or_calculation_pct
  - artifact_ml_or_ai_system_pct
  - artifact_none_pct
  - artifact_other_pct
  - artifact_plan_or_strategy_pct
  - artifact_presentation_or_slides_pct
  - artifact_recipe_or_meal_plan_pct
  - artifact_resume_or_job_application_pct
  - artifact_script_or_snippet_pct
  - artifact_sql_or_database_query_pct
  - artifact_translation_pct
  - artifact_ui_or_design_mockup_pct
  - artifact_video_or_animation_pct
  - collaboration_bucket_augmentation_pct
  - collaboration_bucket_automation_pct
  - collaboration_directive_pct
  - collaboration_feedback_loop_pct
  - collaboration_learning_pct
  - collaboration_none_pct
  - collaboration_task_iteration_pct
  - collaboration_validation_pct
  - human_education_years_mean
  - human_only_ability_pct
  - human_only_time_mean
  - human_with_ai_time_mean
  - multitasking_pct
  - pct
  - usage_pct
  - usage_per_capita_index
  - use_case_coursework_pct
  - use_case_personal_pct
  - use_case_work_pct
- Target slice (soc_occupation, hierarchy_level=0, geo_id=GLOBAL) row count: 68532
- Distinct node_name in slice: 701
- Ten sample node_external_id values: ['49-9021.00', '13-2099.01', '19-3051.00', '53-3031.00', '49-3092.00', '13-1041.00', '19-1041.00', '25-1062.00', '39-3012.00', '29-2051.00']
- Sample occupation for per-date metric listing: Accountants and Auditors
  - 2026-04-01: ['ai_autonomy_mean', 'ai_education_years_mean', 'artifact_academic_paper_or_thesis_pct', 'artifact_advice_or_recommendation_pct', 'artifact_analysis_or_summary_pct', 'artifact_app_or_website_pct', 'artifact_audio_or_music_pct', 'artifact_blog_or_article_pct', 'artifact_chart_or_visualization_pct', 'artifact_code_fix_or_debug_pct', 'artifact_config_or_infra_pct', 'artifact_creative_writing_pct', 'artifact_data_or_spreadsheet_pct', 'artifact_document_or_report_pct', 'artifact_educational_material_pct', 'artifact_email_or_message_pct', 'artifact_explanation_or_answer_pct', 'artifact_game_or_interactive_pct', 'artifact_idea_or_brainstorm_pct', 'artifact_image_or_graphic_pct', 'artifact_marketing_or_social_content_pct', 'artifact_math_or_calculation_pct', 'artifact_ml_or_ai_system_pct', 'artifact_none_pct', 'artifact_other_pct', 'artifact_plan_or_strategy_pct', 'artifact_presentation_or_slides_pct', 'artifact_recipe_or_meal_plan_pct', 'artifact_resume_or_job_application_pct', 'artifact_script_or_snippet_pct', 'artifact_sql_or_database_query_pct', 'artifact_translation_pct', 'artifact_ui_or_design_mockup_pct', 'artifact_video_or_animation_pct', 'collaboration_bucket_augmentation_pct', 'collaboration_bucket_automation_pct', 'collaboration_directive_pct', 'collaboration_feedback_loop_pct', 'collaboration_learning_pct', 'collaboration_none_pct', 'collaboration_task_iteration_pct', 'collaboration_validation_pct', 'human_education_years_mean', 'human_only_ability_pct', 'human_only_time_mean', 'human_with_ai_time_mean', 'multitasking_pct', 'pct', 'use_case_coursework_pct', 'use_case_personal_pct', 'use_case_work_pct']
  - 2026-05-01: ['ai_autonomy_mean', 'ai_education_years_mean', 'artifact_academic_paper_or_thesis_pct', 'artifact_advice_or_recommendation_pct', 'artifact_analysis_or_summary_pct', 'artifact_app_or_website_pct', 'artifact_audio_or_music_pct', 'artifact_blog_or_article_pct', 'artifact_chart_or_visualization_pct', 'artifact_code_fix_or_debug_pct', 'artifact_config_or_infra_pct', 'artifact_creative_writing_pct', 'artifact_data_or_spreadsheet_pct', 'artifact_document_or_report_pct', 'artifact_educational_material_pct', 'artifact_email_or_message_pct', 'artifact_explanation_or_answer_pct', 'artifact_game_or_interactive_pct', 'artifact_idea_or_brainstorm_pct', 'artifact_image_or_graphic_pct', 'artifact_marketing_or_social_content_pct', 'artifact_math_or_calculation_pct', 'artifact_ml_or_ai_system_pct', 'artifact_none_pct', 'artifact_other_pct', 'artifact_plan_or_strategy_pct', 'artifact_presentation_or_slides_pct', 'artifact_recipe_or_meal_plan_pct', 'artifact_resume_or_job_application_pct', 'artifact_script_or_snippet_pct', 'artifact_sql_or_database_query_pct', 'artifact_translation_pct', 'artifact_ui_or_design_mockup_pct', 'artifact_video_or_animation_pct', 'collaboration_bucket_augmentation_pct', 'collaboration_bucket_automation_pct', 'collaboration_directive_pct', 'collaboration_feedback_loop_pct', 'collaboration_learning_pct', 'collaboration_none_pct', 'collaboration_task_iteration_pct', 'collaboration_validation_pct', 'human_education_years_mean', 'human_only_ability_pct', 'human_only_time_mean', 'human_with_ai_time_mean', 'multitasking_pct', 'pct', 'use_case_coursework_pct', 'use_case_personal_pct', 'use_case_work_pct']

## job_exposure.csv
- Header: ['occ_code', 'title', 'observed_exposure']
- Row count: 756
- Ten sample occ_code values: ['11-1011', '11-1021', '11-1031', '11-2011', '11-2021', '11-2022', '11-2032', '11-3012', '11-3013', '11-3021']

## wage_data.csv
- Header: ['SOCcode', 'JobName', 'JobFamily', 'isBright', 'isGreen', 'JobZone', 'MedianSalary', 'JobForecast', 'ChanceAuto', 'WageGroup']
- Row count: 1090
- Ten sample SOCcode values: ['13-2011.01', '13-2011.00', '27-2011.00', '15-2011.00', '29-1199.01', '29-1141.01', '25-2059.01', '51-9191.00', '23-1021.00', '11-3011.00']

## Overlap after normalisation (strip trailing .00)
- claude_ai: slice codes=718, job_exposure match=557 (77.6%), wage_data match=578 (80.5%)
- 1p_api: slice codes=701, job_exposure match=542 (77.3%), wage_data match=559 (79.7%)

## Gate 1 acceptance check

- Deviation from plan: source CSVs are comma-delimited (`sep=","`), not semicolon as plan assumed. Verified by raw header inspection. Used comma for all reads; downstream build_data.py must do the same.
- Row counts: aei_claude_ai=1,636,573 (expected 1,636,573) match. aei_1p_api=491,705 (expected 491,705) match.
- category_name set = {onet, overall, request, soc_occupation} — match.
- date_start set = {2026-04-01, 2026-05-01} — match.
- Metric list: 53 distinct metric_id, includes usage_pct, collaboration_bucket_automation_pct, collaboration_bucket_augmentation_pct, human_only_time_mean, human_with_ai_time_mean, ai_autonomy_mean, use_case_work_pct, and 24 artifact_*_pct metrics — match, exceeds 20 threshold.
- Extra unexpected metric_id observed: bare `pct` (not in plan's named list, not invented by us — present in source, left as-is, not referenced by any panel).
- Target slice (soc_occupation, hierarchy_level=0, geo_id=GLOBAL): claude_ai 72,107 rows / 718 occupations; 1p_api 68,532 rows / 701 occupations. Both >= 500 threshold.
- node_external_id sample format: `NN-NNNN.00` (trailing `.00` present) — confirmed.
- Overlap after stripping trailing `.00`: claude_ai vs job_exposure 77.6%, vs wage_data 80.5%; 1p_api vs job_exposure 77.3%, vs wage_data 79.7%. All >= 60% threshold.
- wage_data.csv header order/columns differ slightly from plan's listed order but all needed columns present: SOCcode, JobName, JobFamily, JobZone, MedianSalary, JobForecast, ChanceAuto (plus extra isBright, isGreen, WageGroup, unused).

**GATE 1: PASS.** Proceeding to Task 2 (build_data.py) using comma delimiter and node_name as the join key for occupation identity (soc code derived from node_external_id, normalised by stripping trailing `.00`).

## Task 2 build decisions (recorded before/after build_data.py)

- Usage metric: within the target slice, metric_id "usage_pct" does not occur (it only
  exists at category_name="overall"). The per-node usage share in the slice is carried
  under metric_id "pct". Verified via per-slice distinct-metric_id check (51 metrics in
  slice vs 53 file-wide; missing two are usage_pct and usage_per_capita_index).
  Decision: keep raw metric_id "pct" verbatim in every occ/<soc>.json metrics blob
  (Rule 2 compliance); use the app-level key "usage_pct" only in index.json's flat
  occupation summaries and as the constant USAGE_METRIC_ID = "pct" in build_data.py /
  app.js, since that is a derived convenience field, not a metric_id.
- Occupation universe: claude_ai slice has 718 distinct node_name/soc, 1p_api has 701;
  1p_api is NOT a subset of claude_ai. Union = 746 distinct soc codes, 1:1 with node_name
  within each source (checked, zero collisions). index.json.occupations has 746 entries;
  this is the number build_data.py's acceptance check must match, not either single-source
  count.
- wage_data.csv sentinels: JobZone==-1 (121 rows) and ChanceAuto==-1.0 (424 rows) are
  "missing", not real values -- omitted from wage.job_zone / wage.chance_auto rather than
  written as -1. JobForecast is a projected-employment count, not a qualitative label, so
  wage.forecast is derived from the isBright boolean column instead ("Bright" / "Not
  bright") rather than reusing JobForecast's numeric value under a mismatched key.
- Neighbours pinned to source=claude_ai, month=2026-05-01 (plan did not specify one).
  Computed for 516 of 746 occupations; the rest lack a wage_data match, a pinned-month
  automation_pct, or no same-JobFamily lower-automation candidate within +-25% salary.
