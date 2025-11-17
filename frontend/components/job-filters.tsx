"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import { X, Filter } from "lucide-react";
import type { JobFilters } from "@/lib/api";

const JOB_CATEGORIES = [
  "Blockchain/Crypto",
  "AI/ML",
  "Data Engineering",
  "Full Stack",
  "Frontend",
  "Backend",
  "DevOps/SRE",
  "Mobile",
  "Product/Design",
];

const WORK_ARRANGEMENTS = ["Remote", "Hybrid", "On-site"];

interface JobFiltersComponentProps {
  filters: JobFilters;
  onFiltersChange: (filters: JobFilters) => void;
  onClearFilters: () => void;
}

export default function JobFiltersComponent({
  filters,
  onFiltersChange,
  onClearFilters,
}: JobFiltersComponentProps) {
  const [technologyInput, setTechnologyInput] = useState("");
  const [skillInput, setSkillInput] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCategoryToggle = (category: string) => {
    const current = filters.job_categories || [];
    const updated = current.includes(category)
      ? current.filter((c) => c !== category)
      : [...current, category];
    onFiltersChange({ ...filters, job_categories: updated });
  };

  const handleAddTechnology = () => {
    if (!technologyInput.trim()) return;
    const current = filters.technologies || [];
    if (!current.includes(technologyInput.trim())) {
      onFiltersChange({
        ...filters,
        technologies: [...current, technologyInput.trim()],
      });
    }
    setTechnologyInput("");
  };

  const handleRemoveTechnology = (tech: string) => {
    const current = filters.technologies || [];
    onFiltersChange({
      ...filters,
      technologies: current.filter((t) => t !== tech),
    });
  };

  const handleAddSkill = () => {
    if (!skillInput.trim()) return;
    const current = filters.required_skills || [];
    if (!current.includes(skillInput.trim())) {
      onFiltersChange({
        ...filters,
        required_skills: [...current, skillInput.trim()],
      });
    }
    setSkillInput("");
  };

  const handleRemoveSkill = (skill: string) => {
    const current = filters.required_skills || [];
    onFiltersChange({
      ...filters,
      required_skills: current.filter((s) => s !== skill),
    });
  };

  const activeFilterCount = [
    filters.job_categories?.length ?? 0,
    filters.technologies?.length ?? 0,
    filters.required_skills?.length ?? 0,
    filters.work_arrangement ? 1 : 0,
    filters.min_years_experience !== undefined ? 1 : 0,
    filters.independent_contractor_friendly !== undefined ? 1 : 0,
    filters.has_own_products !== undefined ? 1 : 0,
    filters.is_recruiting_company !== undefined ? 1 : 0,
    filters.min_employee_size !== undefined ? 1 : 0,
    // Don't count max_employee_size when it's 111 (the default)
    filters.max_employee_size !== undefined && filters.max_employee_size !== 111 ? 1 : 0,
  ].reduce((sum: number, count: number) => sum + count, 0);

  return (
    <div className="rounded-lg border bg-card p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Filters</h3>
          {activeFilterCount > 0 && (
            <Badge variant="secondary">{activeFilterCount} active</Badge>
          )}
        </div>
        <div className="flex gap-2">
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" onClick={onClearFilters}>
              Clear All
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? "Collapse" : "Expand"}
          </Button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-6">
          {/* Job Categories */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Job Categories
            </Label>
            <div className="flex flex-wrap gap-2">
              {JOB_CATEGORIES.map((category) => {
                const isSelected = filters.job_categories?.includes(category);
                return (
                  <Badge
                    key={category}
                    variant={isSelected ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => handleCategoryToggle(category)}
                  >
                    {category}
                    {isSelected && <X className="ml-1 h-3 w-3" />}
                  </Badge>
                );
              })}
            </div>
          </div>

          {/* Technologies */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Technologies
            </Label>
            <div className="flex gap-2 mb-2">
              <Input
                type="text"
                placeholder="Add technology (e.g., React, Python)"
                value={technologyInput}
                onChange={(e) => setTechnologyInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTechnology();
                  }
                }}
              />
              <Button onClick={handleAddTechnology} size="sm">
                Add
              </Button>
            </div>
            {filters.technologies && filters.technologies.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {filters.technologies.map((tech) => (
                  <Badge key={tech} variant="secondary">
                    {tech}
                    <X
                      className="ml-1 h-3 w-3 cursor-pointer"
                      onClick={() => handleRemoveTechnology(tech)}
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Required Skills */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Required Skills
            </Label>
            <div className="flex gap-2 mb-2">
              <Input
                type="text"
                placeholder="Add skill"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
              />
              <Button onClick={handleAddSkill} size="sm">
                Add
              </Button>
            </div>
            {filters.required_skills && filters.required_skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {filters.required_skills.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                    <X
                      className="ml-1 h-3 w-3 cursor-pointer"
                      onClick={() => handleRemoveSkill(skill)}
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Work Arrangement */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Work Arrangement
            </Label>
            <Select
              value={filters.work_arrangement || "any"}
              onValueChange={(value: string) =>
                onFiltersChange({
                  ...filters,
                  work_arrangement: value === "any" ? undefined : value,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                {WORK_ARRANGEMENTS.map((arrangement) => (
                  <SelectItem key={arrangement} value={arrangement}>
                    {arrangement}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Years of Experience */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Minimum Years of Experience:{" "}
              {filters.min_years_experience !== undefined
                ? filters.min_years_experience
                : "Any"}
            </Label>
            <div className="flex items-center gap-4">
              <Slider
                value={[filters.min_years_experience || 0]}
                onValueChange={([value]: number[]) =>
                  onFiltersChange({
                    ...filters,
                    min_years_experience: value === 0 ? undefined : value,
                  })
                }
                max={15}
                step={1}
                className="flex-1"
              />
              {filters.min_years_experience !== undefined && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    onFiltersChange({
                      ...filters,
                      min_years_experience: undefined,
                    })
                  }
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Employee Size */}
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Company Employee Size (1-500 range)
            </Label>
            <div className="space-y-3">
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">
                  Minimum:{" "}
                  {filters.min_employee_size !== undefined
                    ? filters.min_employee_size.toLocaleString()
                    : "Any"}
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[filters.min_employee_size || 1]}
                    onValueChange={([value]: number[]) =>
                      onFiltersChange({
                        ...filters,
                        min_employee_size: value === 1 ? undefined : value,
                      })
                    }
                    min={1}
                    max={500}
                    step={10}
                    className="flex-1"
                  />
                  {filters.min_employee_size !== undefined && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        onFiltersChange({
                          ...filters,
                          min_employee_size: undefined,
                        })
                      }
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">
                  Maximum:{" "}
                  {filters.max_employee_size !== undefined
                    ? filters.max_employee_size.toLocaleString()
                    : "111 (default)"}
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[filters.max_employee_size ?? 111]}
                    onValueChange={([value]: number[]) =>
                      onFiltersChange({
                        ...filters,
                        max_employee_size: value === 111 ? 111 : value,
                      })
                    }
                    min={1}
                    max={500}
                    step={10}
                    className="flex-1"
                  />
                  {filters.max_employee_size !== 111 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        onFiltersChange({
                          ...filters,
                          max_employee_size: 111,
                        })
                      }
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Additional Checkboxes */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="contractor"
                checked={filters.independent_contractor_friendly === true}
                onCheckedChange={(checked: boolean) =>
                  onFiltersChange({
                    ...filters,
                    independent_contractor_friendly: checked
                      ? true
                      : undefined,
                  })
                }
              />
              <Label
                htmlFor="contractor"
                className="text-sm font-normal cursor-pointer"
              >
                Independent Contractor Friendly
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="has-products"
                checked={filters.has_own_products === true}
                onCheckedChange={(checked: boolean) =>
                  onFiltersChange({
                    ...filters,
                    has_own_products: checked ? true : undefined,
                  })
                }
              />
              <Label
                htmlFor="has-products"
                className="text-sm font-normal cursor-pointer"
              >
                Company Has Own Products
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="not-recruiting"
                checked={filters.is_recruiting_company === false}
                onCheckedChange={(checked: boolean) =>
                  onFiltersChange({
                    ...filters,
                    is_recruiting_company: checked ? false : undefined,
                  })
                }
              />
              <Label
                htmlFor="not-recruiting"
                className="text-sm font-normal cursor-pointer"
              >
                Exclude Recruiting Companies
              </Label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

