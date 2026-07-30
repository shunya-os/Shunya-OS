/** UBME TypeScript types matching backend models. */

export interface FieldDef {
  key: string;
  label: string;
  field_type: string;
  required?: boolean;
  unique?: boolean;
  default?: any;
  options?: string[];
  placeholder?: string;
  help_text?: string;
  validation?: Record<string, any>;
  ai_generated?: boolean;
  computed_formula?: string;
  relationship_type?: string;
  target_object_type?: string;
  display_in_list?: boolean;
  searchable?: boolean;
  order?: number;
}

export interface ObjectTypeDef {
  key: string;
  name: string;
  plural_name?: string;
  description?: string;
  icon?: string;
  color?: string;
  category?: string;
  fields: FieldDef[];
  relationships?: Record<string, any>[];
  lifecycle?: string[];
  ownership?: string;
  searchable?: boolean;
  ai_semantics?: Record<string, any>;
  default_view?: string;
  group_by_field?: string;
  calendar_field?: string;
  map_field?: string;
  actions?: ActionDef[];
}

export interface ViewDef {
  key: string;
  label: string;
  view_type: string;
  object_type: string;
  fields: string[];
  filters?: Record<string, any>;
  sort_by?: string;
  group_by?: string;
  is_default?: boolean;
}

export interface WorkflowStateDef {
  key: string;
  label: string;
  state_type: string;
}

export interface WorkflowTransitionDef {
  from_state: string;
  to_state: string;
  label: string;
  requires_approval?: boolean;
  condition?: string;
  trigger?: string;
}

export interface WorkflowDef {
  key: string;
  name: string;
  object_type: string;
  states: WorkflowStateDef[];
  transitions: WorkflowTransitionDef[];
  default_state?: string;
}

export interface NavigationEntry {
  label: string;
  object_type: string;
  icon: string;
}

export interface ActionDef {
  key: string;
  label: string;
  icon?: string;
  endpoint?: string;
  method?: string;
  requires_confirmation?: boolean;
  requires_approval?: boolean;
  available_when?: string;
}

export interface DashboardCard {
  key: string;
  label: string;
  card_type: string;
  object_type?: string;
  field?: string;
  filter_criteria?: string;
  icon?: string;
  value?: any;
}

export interface ModuleDef {
  key: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  navigation?: NavigationEntry[];
  object_types?: ObjectTypeDef[];
  views?: ViewDef[];
  workflows?: WorkflowDef[];
  dashboard_config?: Record<string, any>;
  template_source?: string;
  created_at?: string;
  updated_at?: string;
  dashboard_cards?: DashboardCard[];
}

export interface BusinessTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  industry: string;
  module: ModuleDef;
}

export interface ObjectInstance {
  id: string;
  object_type: string;
  module_key: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  data: Record<string, any>;
}

export interface NavGroup {
  name: string;
  icon: string;
  color: string;
  entries: NavigationEntry[];
}