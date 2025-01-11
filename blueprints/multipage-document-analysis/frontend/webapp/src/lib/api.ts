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

import { JobStatus } from "@/types";
import { get } from "aws-amplify/api";
import axios from "axios";
import { fetchAuthSession } from "aws-amplify/auth";

export interface TableItem {
  id: string;
  status: JobStatus;
  jobDescription?: string;
  userDescription?: string;
}

// Simulate API delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function generateMockData(count: number = 25): TableItem[] {
  const descriptions = [
    "Data transformation pipeline",
    "Image batch processing",
    "Document conversion task",
    "Video transcoding job",
    "Log file analysis",
  ];

  const userNotes = [
    "High priority batch",
    "Large dataset processing",
    "Retry after optimization",
    "Weekly scheduled job",
    "Custom parameters applied",
  ];

  return Array.from({ length: count }, (_, index) => ({
    id: `JOB-${String(index + 1).padStart(4, "0")}`,
    status:
      Object.values(JobStatus)[
        Math.floor(Math.random() * Object.values(JobStatus).length)
      ],
    jobDescription:
      descriptions[Math.floor(Math.random() * descriptions.length)],
    userDescription:
      Math.random() > 0.3
        ? userNotes[Math.floor(Math.random() * userNotes.length)]
        : undefined,
  }));
}

export const api = {
  listJobs: async (): Promise<TableItem[]> => {
    await delay(1000); // Simulate network latency
    return generateMockData();
  },
};

interface PresignedPostData {
  url: string;
  fields: {
    key: string;
    'x-amz-algorithm': string;
    'x-amz-credential': string;
    'x-amz-date': string;
    'x-amz-security-token': string;
    policy: string;
    'x-amz-signature': string;
  };
}

interface UploadURLResponse {
  presigned_post: PresignedPostData;
}

export async function getUploadURL(filename: string): Promise<PresignedPostData> {
  console.log('Requesting upload URL for file:', filename);

  const { body } = await get({
    apiName: "Backend",
    path: `/multipage-doc-analysis/upload/pdf-files/${filename}`,
  }).response;

  const jsonData = await body.json() as unknown;
  console.log('Received response:', jsonData);

  if (isUploadURLResponse(jsonData)) {
    console.log('Presigned post data:', JSON.stringify(jsonData.presigned_post, null, 2));
    return jsonData.presigned_post;
  } else {
    console.error('Invalid response:', jsonData);
    throw new Error('Invalid response format from server');
  }
}

function isUploadURLResponse(data: unknown): data is UploadURLResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'presigned_post' in data &&
    typeof (data as UploadURLResponse).presigned_post === 'object' &&
    (data as UploadURLResponse).presigned_post !== null &&
    'url' in (data as UploadURLResponse).presigned_post &&
    'fields' in (data as UploadURLResponse).presigned_post
  );
}


export async function uploadFile(file: File, presignedPostData: PresignedPostData) {
  const formData = new FormData();
  
  // Append all fields from presignedPostData.fields to the form data
  Object.entries(presignedPostData.fields).forEach(([key, value]) => {
    formData.append(key, value);
  });
  
  // Append the file last
  formData.append('file', file);

  // Use fetch or axios to make the POST request
  const response = await fetch(presignedPostData.url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }
  
  return response;
}

interface StartDocumentAnalysisRequest {
  key: string;
  metadata?: {
    filename?: string;
  };
}

export async function startDocumentAnalysis(
  input: StartDocumentAnalysisRequest,
): Promise<void> {
  await axios.post(
    `${import.meta.env.VITE_API_GATEWAY_REST_API_ENDPOINT}/multipage-doc-analysis/processDocument`,
    input,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${(await fetchAuthSession()).tokens?.idToken?.toString()}`,
      },
    },
  );
}

export type Job = {
  document_name: string;
  document_key: string;
  id: string;
  report_key: string;
  status: string;
  created_at?: string;
  updated_at?: string;
};

export type JobsResponse = {
  items: Job[];
};

export async function getJobs() {
  const { body } = await get({
    apiName: "Backend",
    path: "/multipage-doc-analysis/jobs/query",
  }).response;
  return body.json() as Promise<JobsResponse>;
}

export type DownloadURLResponse = {
  presigned_url: string;
};

export async function downloadFile(
  type: "document" | "report",
  fileKey: string,
) {
  const { body } = await get({
    apiName: "Backend",
    path: `/multipage-doc-analysis/download/${type}/${fileKey}`,
  }).response;

  return body.json() as Promise<DownloadURLResponse>;
}

export type JobResults = {
  job_id: string;
  json_report: {
    general_information: {
      name: string;
      expedition_date: string;
      expedition_city: string;
      duration: string;
      social_object: string[];
      nationality: string;
      open_to_foreigners: boolean;
      fixed_social_capital: string;
      total_stock: string;
    };
    shareholders: {
      shareholders: Array<{
        shareholder_name: string;
        stock_units: string;
        stocks_value: string;
      }>;
    };
    administration: {
      managers: Array<{
        name: string;
        position: string;
        powers: string[];
      }>;
    };
    legal_representative: {
      name: string;
      position: string;
      powers: string[];
    };
    notary_information: {
      notary_name: string;
      document_number: string;
      notary_number: string;
      entity_of_creation: string;
    };
  };
};

export async function getJobResults(jobId: string) {
  const { body } = await get({
    apiName: "Backend",
    path: `/multipage-doc-analysis/jobs/results/${jobId}`,
  }).response;
  return body.json() as Promise<JobResults>;
}
