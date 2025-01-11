// MIT No Attribution
//
// Copyright 2024 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Loader2,
  SearchIcon,
  RotateCw,
  FileDown,
  FileJson,
  FileType,
} from "lucide-react";
import { useState, Suspense } from "react";
import { useLoaderData, Await, useRevalidator } from "react-router-dom";

import {
  Pagination,
  PaginationContent,
  // PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";

import {
  getUploadURL,
  uploadFile,
  startDocumentAnalysis,
  Job,
  JobsResponse,
  downloadFile,
  getJobResults,
  JobResults,
} from "@/lib/api";
// import { JobStatus } from "@/types";
import { v4 as uuidv4 } from "uuid";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useTranslation } from "react-i18next";

interface Sort {
  key: keyof Job;
  order: "asc" | "desc";
}

interface SelectedJob extends Job {
  created_at?: string;
  updated_at?: string;
}

const List: React.FC = () => {
  const loaderData = useLoaderData() as { items: Promise<JobsResponse> };

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<Sort>({
    key: "document_name",
    order: "asc",
  });
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const { toast } = useToast();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const revalidator = useRevalidator();
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [selectedJobResults, setSelectedJobResults] =
    useState<JobResults | null>(null);
  const [loadingResultsIds, setLoadingResultsIds] = useState<Set<string>>(
    new Set(),
  );
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<SelectedJob | null>(null);

  const { t } = useTranslation();

  const filteredAndSortedItems = (itemList: Job[]) => {
    return itemList
      .filter((item) => {
        const searchValue = search.toLowerCase();
        return (
          item.id.toLowerCase().includes(searchValue) ||
          item.status.toLowerCase().includes(searchValue) ||
          item.document_name.toLowerCase().includes(searchValue)
        );
      })
      .sort((a, b) => {
        const aValue = a[sort.key];
        const bValue = b[sort.key];
        if (typeof aValue === "string" && typeof bValue === "string") {
          return sort.order === "asc"
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }
        return 0;
      });
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    // Add timestamp to filename
    const now = new Date();
    const timestamp = now
      .toISOString()
      .replace(/T/, "-")
      .replace(/\..+/, "")
      .replace(/:/g, "-");
    setFileName(`${timestamp}-${file.name}`);
    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      return;
    }

    if (!selectedFile.type.includes("pdf")) {
      toast({
        title: t("toasts.invalidFileType.title"),
        description: t("toasts.invalidFileType.description"),
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    const fileId = uuidv4();
    const s3Key = `${fileId}.pdf`;

    try {
      // Step 1: Get presigned URL
      console.debug("[FileUpload] Requesting presigned URL");
      const presignedPostData = await getUploadURL(s3Key);

      // Step 2: Upload file to S3
      console.debug("[FileUpload] Uploading file to S3");
      await uploadFile(selectedFile, presignedPostData);
      console.info("[FileUpload] File uploaded successfully");

      // Step 3: Start document analysis
      console.debug("[FileUpload] Initiating document analysis");
      await startDocumentAnalysis({
        key: `pdf-files/${s3Key}`,
        metadata: {
          filename: fileName,
        },
      });

      console.info("[FileUpload] Document analysis started", { fileId });
      toast({
        title: t("toasts.uploadSuccess.title"),
        description: t("toasts.uploadSuccess.description"),
        variant: "default",
      });
      setIsDialogOpen(false);
      revalidator.revalidate();
    } catch (error) {
      console.error("[FileUpload] Process failed", {
        fileId,
        error: error instanceof Error ? error.message : "Unknown error",
      });
      toast({
        title: t("toasts.uploadError.title"),
        description: t("toasts.uploadError.description"),
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      setSelectedFile(null);
      setFileName("");
    }
  };

  const handleDownload = async (
    type: "document" | "report",
    documentKey: string,
    jobId: string,
  ) => {
    // Clear the downloading state for this document key first as a safety measure
    setDownloadingIds((prev) => {
      const next = new Set(prev);
      next.delete(documentKey);
      return next;
    });

    if (downloadingIds.size > 0) {
      toast({
        title: t("toasts.downloadInProgress.title"),
        description: t("toasts.downloadInProgress.description"),
        variant: "destructive",
      });
      return;
    }

    setDownloadingIds((prev) => new Set(prev).add(documentKey));

    try {
      const { presigned_url } = await downloadFile(type, documentKey);
      const response = await fetch(presigned_url);
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();

      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;

      const extension = "pdf";
      const fileName = `${jobId}-${type}.${extension}`;

      link.setAttribute("download", fileName);

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up the blob URL after download starts
      setTimeout(() => {
        window.URL.revokeObjectURL(blobUrl);
      }, 1500);
    } catch (error) {
      console.error("Failed to download document", error);
      toast({
        title: t("toasts.downloadError.title"),
        description: t("toasts.downloadError.description"),
        variant: "destructive",
      });
    } finally {
      setDownloadingIds((prev) => {
        const next = new Set(prev);
        next.delete(documentKey);
        return next;
      });
    }
  };

  const handleViewResults = async (job: SelectedJob) => {
    setLoadingResultsIds((prev) => new Set(prev).add(job.id));
    try {
      const results = await getJobResults(job.id);
      setSelectedJobResults(results);
      setSelectedJob(job);
      setIsSheetOpen(true);
    } catch (error) {
      console.error("Failed to fetch job results", error);
      toast({
        title: t("toasts.resultsError.title"),
        description: t("toasts.resultsError.description"),
        variant: "destructive",
      });
    } finally {
      setLoadingResultsIds((prev) => {
        const next = new Set(prev);
        next.delete(job.id);
        return next;
      });
    }
  };

  return (
    <main className="flex-1 p-4 md:p-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">{t("list.title")}</h1>
          <Suspense
            fallback={
              <Badge>
                <Loader2 className="h-4 w-4 animate-spin" />
              </Badge>
            }
          >
            <Await resolve={loaderData.items}>
              {(resolvedItems: JobsResponse) => (
                <Badge className="bg-primary text-white">
                  {resolvedItems.items.length}
                </Badge>
              )}
            </Await>
          </Suspense>
        </div>
        <div className="flex gap-4">
          <div className="relative flex-1 md:max-w-xs">
            <SearchIcon className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder={t("list.searchPlaceholder")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => revalidator.revalidate()}
                  disabled={revalidator.state === "loading"}
                >
                  <RotateCw
                    className={`h-4 w-4 ${revalidator.state === "loading" ? "animate-spin" : ""}`}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{t("list.refreshTooltip")}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>{t("list.createNewJob")}</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t("jobDialog.title")}</DialogTitle>
                <DialogDescription>
                  {t("jobDialog.description")}
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label
                      htmlFor="file-upload"
                      className="text-sm font-medium"
                    >
                      {t("jobDialog.form.fileUpload.label")}
                    </label>
                    <Input
                      id="file-upload"
                      type="file"
                      accept=".pdf"
                      onChange={handleFileSelect}
                      disabled={isUploading}
                      className="max-w-xs"
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="file-name" className="text-sm font-medium">
                      {t("jobDialog.form.fileName.label")}
                      <br />
                      <span className="text-xs text-muted-foreground">
                        {t("jobDialog.form.fileName.description")}
                      </span>
                    </label>
                    <Input
                      id="file-name"
                      type="text"
                      value={fileName}
                      onChange={(e) => setFileName(e.target.value)}
                      placeholder={t("jobDialog.form.fileName.placeholder")}
                      disabled={isUploading || !selectedFile}
                      className="max-w-xs"
                    />
                  </div>
                  {isUploading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>{t("jobDialog.form.uploading.status")}</span>
                    </div>
                  )}
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={!selectedFile || isUploading}>
                    {isUploading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {t("jobDialog.form.uploading.buttonText")}
                      </>
                    ) : (
                      t("jobDialog.form.submit")
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <Card className="shadow-xl">
        <Suspense fallback={<DataTableSkeleton />}>
          <Await resolve={loaderData.items}>
            {(resolvedItems: JobsResponse) => {
              const filteredItems = filteredAndSortedItems(resolvedItems.items);
              const totalPages = Math.ceil(filteredItems.length / pageSize);
              const paginatedItems = filteredItems.slice(
                (page - 1) * pageSize,
                page * pageSize,
              );

              return (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {(
                          [
                            "document_name",
                            "status",
                            "id",
                            "document_key",
                            "report",
                          ] as const
                        ).map((key) => (
                          <TableHead
                            key={key}
                            className={`cursor-pointer ${
                              key === "document_key" || key === "report"
                                ? "text-center"
                                : ""
                            }`}
                            onClick={() =>
                              key !== "report"
                                ? setSort({
                                    key: key,
                                    order:
                                      sort.key === key
                                        ? sort.order === "asc"
                                          ? "desc"
                                          : "asc"
                                        : "asc",
                                  })
                                : undefined
                            }
                          >
                            {t(
                              `list.table.${
                                key === "document_key"
                                  ? "document"
                                  : key === "report"
                                    ? "report"
                                    : key
                              }`,
                            )}
                            {sort.key === key && (
                              <span className="ml-1">
                                {sort.order === "asc" ? "\u2191" : "\u2193"}
                              </span>
                            )}
                          </TableHead>
                        ))}
                        <TableHead className="text-center">
                          {t("list.table.results")}
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedItems.map((item) => (
                        <TableRow key={item.id} className="hover:bg-violet-50">
                          <TableCell>
                            <button
                              onClick={() =>
                                handleDownload(
                                  "document",
                                  item.document_key,
                                  item.id,
                                )
                              }
                              className="block w-full truncate text-left text-violet-600 hover:underline"
                              disabled={downloadingIds.has(item.document_key)}
                            >
                              {item.document_name.length > 50
                                ? `${item.document_name.substring(0, 50)}...`
                                : item.document_name}
                            </button>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                item.status === "IN_PROGRESS"
                                  ? "secondary"
                                  : item.status === "PDF_GENERATION"
                                    ? "default"
                                    : item.status === "FAILED"
                                      ? "destructive"
                                      : "outline"
                              }
                            >
                              {item.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[200px]">
                            <code className="inline-block max-w-full truncate rounded bg-muted px-2 py-1 font-mono text-xs">
                              {item.id}
                            </code>
                          </TableCell>
                          <TableCell className="text-center">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="icon"
                                    className="mx-auto rounded-full bg-violet-500 text-white hover:bg-violet-600 active:bg-violet-700"
                                    disabled={downloadingIds.has(
                                      item.document_key,
                                    )}
                                    onClick={() =>
                                      handleDownload(
                                        "document",
                                        item.document_key,
                                        item.id,
                                      )
                                    }
                                  >
                                    {downloadingIds.has(item.document_key) ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <FileDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{t("tooltips.downloadDocument")}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableCell>
                          <TableCell className="text-center">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="icon"
                                    className="mx-auto rounded-full bg-violet-500 text-white hover:bg-violet-600 active:bg-violet-700"
                                    disabled={
                                      item.status !== "PDF_GENERATION" ||
                                      downloadingIds.has(item.report_key)
                                    }
                                    onClick={() =>
                                      handleDownload(
                                        "report",
                                        item.report_key,
                                        item.id,
                                      )
                                    }
                                  >
                                    {downloadingIds.has(item.report_key) ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <FileDown className="h-4 w-4" />
                                    )}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{t("tooltips.downloadReport")}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableCell>
                          <TableCell className="text-center">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="icon"
                                    className="mx-auto rounded-full bg-violet-500 text-white hover:bg-violet-600 active:bg-violet-700"
                                    disabled={
                                      item.status !== "PDF_GENERATION" ||
                                      loadingResultsIds.has(item.id)
                                    }
                                    onClick={() => handleViewResults(item)}
                                  >
                                    {loadingResultsIds.has(item.id) ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <FileJson className="h-4 w-4" />
                                    )}
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>{t("tooltips.viewResults")}</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <CardFooter className="flex items-center justify-between border-t py-3">
                    <div className="w-full text-sm text-muted-foreground">
                      {t("list.pagination.showing")} {(page - 1) * pageSize + 1}{" "}
                      {t("list.pagination.to")}{" "}
                      {Math.min(page * pageSize, filteredItems.length)}{" "}
                      {t("list.pagination.of")} {filteredItems.length}{" "}
                      {t("list.pagination.items")}
                    </div>
                    <Pagination className="flex justify-end">
                      <PaginationContent>
                        <PaginationItem>
                          <PaginationPrevious
                            className="cursor-pointer"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                          />
                        </PaginationItem>
                        {/* Add page numbers */}
                        {Array.from(
                          { length: totalPages },
                          (_, i) => i + 1,
                        ).map((pageNumber) => (
                          <PaginationItem key={pageNumber}>
                            <PaginationLink
                              className="cursor-pointer"
                              onClick={() => setPage(pageNumber)}
                              isActive={pageNumber === page}
                            >
                              {pageNumber}
                            </PaginationLink>
                          </PaginationItem>
                        ))}
                        <PaginationItem>
                          <PaginationNext
                            className="cursor-pointer"
                            onClick={() =>
                              setPage((p) => Math.min(totalPages, p + 1))
                            }
                          />
                        </PaginationItem>
                      </PaginationContent>
                    </Pagination>
                  </CardFooter>
                </>
              );
            }}
          </Await>
        </Suspense>
      </Card>
      <Sheet open={isSheetOpen} onOpenChange={setIsSheetOpen}>
        <SheetContent className="w-[800px] sm:w-[900px] lg:w-[1100px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2 text-xl">
              <FileJson className="h-5 w-5 text-violet-500" />
              {t("resultsSheet.title")}
            </SheetTitle>
            {selectedJob && (
              <>
                <SheetDescription className="flex gap-2 text-wrap rounded-lg border bg-violet-50 p-4">
                  <FileType className="h-4 w-4 text-violet-500" />
                  {selectedJob.document_name}
                </SheetDescription>

                <div className="rounded-lg border bg-slate-950 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="flex items-center gap-2 text-sm font-medium text-slate-200">
                      <FileJson className="h-4 w-4 text-violet-400" />
                      {t("resultsSheet.json.title")}
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 text-xs text-slate-400 hover:bg-transparent hover:text-slate-100"
                      onClick={() => {
                        if (selectedJobResults) {
                          navigator.clipboard.writeText(
                            JSON.stringify(
                              selectedJobResults.json_report,
                              null,
                              2,
                            ),
                          );
                          toast({
                            title: t("resultsSheet.json.copySuccess.title"),
                            description: t(
                              "resultsSheet.json.copySuccess.description",
                            ),
                          });
                        }
                      }}
                    >
                      {t("resultsSheet.json.copyButton")}
                    </Button>
                  </div>
                  <ScrollArea className="h-[calc(100vh-350px)]">
                    <pre className="text-sm">
                      <code className="text-slate-50">
                        {selectedJobResults &&
                          JSON.stringify(
                            selectedJobResults.json_report,
                            null,
                            2,
                          )}
                      </code>
                    </pre>
                  </ScrollArea>
                </div>
              </>
            )}
          </SheetHeader>
        </SheetContent>
      </Sheet>
    </main>
  );
};

interface DataTableSkeletonProps {
  columns?: number;
  rows?: number;
}

export function DataTableSkeleton({
  columns = 4,
  rows = 10,
}: DataTableSkeletonProps) {
  return (
    <div className="p-4">
      <div className="flex flex-col items-center justify-center">
        <div className="flex w-full flex-col items-center gap-2">
          <Skeleton className="h-16 w-full bg-indigo-800 bg-opacity-10" />

          {[...Array(rows)].map((_, rowIndex) => (
            <div key={rowIndex} className="flex w-full gap-2">
              {[...Array(columns)].map((_, colIndex) => (
                <Skeleton
                  key={colIndex}
                  className="h-10 w-full bg-indigo-800 bg-opacity-10"
                />
              ))}
            </div>
          ))}

          <Skeleton className="h-16 w-full bg-indigo-800 bg-opacity-10" />
        </div>
      </div>
    </div>
  );
}

export default List;
