"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "@/store/store";
import {
  fetchProjects,
  setCurrentProject,
  type Project,
} from "@/store/features/projects/projectsSlice";
import { clearAnalysisData } from "@/store/features/analysis/analysisSlice";
import { clearCurrentProjectUserStories } from "@/store/features/userStories/userStoriesSlice";
import { DashboardComponent } from "@/components/ui/dashboard/Dashboard";
import {
  decryptProjectId,
  isValidEncryptedId,
  encryptProjectId,
} from "@/lib/encryption";
import { ArrowLeft, AlertCircle, Loader2 } from "lucide-react";

export default function ProjectDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const dispatch = useDispatch<AppDispatch>();

  const { projects, loading: projectsLoading } = useSelector(
    (state: RootState) => state.projects
  );
  const { loading: analysisLoading } = useSelector(
    (state: RootState) => state.analysis
  );

  const [projectId, setProjectId] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [decryptionError, setDecryptionError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Refs to prevent duplicate operations
  const initializedProjectRef = useRef<string | null>(null);
  const hasFetchedProjectsRef = useRef(false);

  // Decrypt project ID from URL params
  useEffect(() => {
    const encryptedId = params.id as string;

    if (!encryptedId) {
      setDecryptionError("No project ID provided");
      return;
    }

    try {
      // Try to decrypt the ID
      if (isValidEncryptedId(encryptedId)) {
        const decryptedId = decryptProjectId(encryptedId);
        setProjectId(decryptedId);
        setDecryptionError(null);
      } else {
        // If decryption fails, treat as plain ID (fallback for development)
        console.warn("Using unencrypted project ID as fallback");
        setProjectId(encryptedId);
        setDecryptionError(null);
      }
    } catch (error) {
      console.error("Failed to decrypt project ID:", error);
      setDecryptionError("Invalid project ID");
    }
  }, [params.id]);

  // Fetch projects if not already loaded
  useEffect(() => {
    // Only fetch once
    if (hasFetchedProjectsRef.current) return;
    if (projects.length > 0) return; // Already have projects
    if (projectsLoading) return; // Already loading

    hasFetchedProjectsRef.current = true;
    dispatch(fetchProjects());
  }, [dispatch, projects.length, projectsLoading]);

  // Find and set the current project
  useEffect(() => {
    if (!projectId) return;

    // Prevent re-initialization if already initialized for this project
    if (initializedProjectRef.current === projectId) return;

    // If no projects loaded yet, wait for them
    if (projects.length === 0 && projectsLoading) return;

    const foundProject = projects.find((p) => p.id === projectId);

    if (foundProject) {
      setProject(foundProject);
      dispatch(setCurrentProject(foundProject));

      // Store in localStorage for compatibility with existing components
      if (typeof window !== "undefined") {
        localStorage.setItem("project_id", projectId);
        if (foundProject.name) {
          localStorage.setItem("selected_project_name", foundProject.name);
        }
      }

      // Clear previous analysis data when switching projects
      dispatch(clearAnalysisData());
      dispatch(clearCurrentProjectUserStories());

      initializedProjectRef.current = projectId;
      setIsInitialized(true);
    } else if (!projectsLoading) {
      // Project not found after projects are loaded
      // Try to refetch projects once in case it's a newly created project
      if (!hasFetchedProjectsRef.current) {
        console.log('Project not found, refetching projects...');
        hasFetchedProjectsRef.current = true;
        dispatch(fetchProjects());
      } else {
        setDecryptionError("Project not found");
      }
    }
  }, [projectId, projects, dispatch, projectsLoading]);

  // Handle project selection from dropdown (when user changes project)
  const handleProjectSelect = useCallback(
    (newProjectId: string) => {
      try {
        const encryptedId = encryptProjectId(newProjectId);
        router.replace(`/projects/${encryptedId}/dashboard`);
      } catch (error) {
        console.error("Failed to navigate to new project:", error);
        // Fallback to unencrypted ID
        router.replace(`/projects/${newProjectId}/dashboard`);
      }
    },
    [router]
  );

  // Enhanced DashboardComponent with project selection handling
  const EnhancedDashboard = useMemo(() => {
    if (!project || !isInitialized) return null;

    return (
      <DashboardComponent
        skipBootstrapFetches
        onProjectSelect={handleProjectSelect}
        initialProjectId={project.id}
      />
    );
  }, [project?.id, isInitialized, handleProjectSelect]);

  // Loading state - only show full screen loader for initial project loading
  // Analysis loading is handled within the Dashboard component itself
  if ((projectsLoading && projects.length === 0) || !isInitialized) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            {projectsLoading ? "Loading projects..." : "Initializing dashboard..."}
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (decryptionError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Project Not Found
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            {decryptionError === "Invalid project ID"
              ? "The project link appears to be invalid or corrupted."
              : decryptionError === "Project not found"
              ? "This project may have been deleted or you may not have access to it."
              : decryptionError}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push("/projects")}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white rounded-lg hover:shadow-lg transition-all duration-200"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Projects
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Project not found (but no decryption error)
  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Project Not Found
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            The requested project could not be found. It may have been deleted
            or you may not have access to it.
          </p>
          <button
            onClick={() => router.push("/projects")}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white rounded-lg hover:shadow-lg transition-all duration-200 mx-auto"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Project Header */}
      {/* <div className="flex items-center gap-4">
        <button
          onClick={() => router.push("/projects")}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          title="Back to Projects"
        >
          <ArrowLeft className="w-5 h-5" />
          Projects
        </button>
      </div> */}
      {/* Dashboard Content */}
      {EnhancedDashboard}
    </div>
  );
}
