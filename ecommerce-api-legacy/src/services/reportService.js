class ReportService {
  constructor(reportRepository) {
    this.reports = reportRepository;
  }

  async financialReport() {
    const rows = await this.reports.courseFinancials();
    const byCourse = new Map();

    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
      }
      const data = byCourse.get(row.course_id);
      if (row.enrollment_id != null) {
        if (row.status === 'PAID') data.revenue += row.amount;
        data.students.push({
          student: row.student_name || 'Unknown',
          paid: row.amount != null ? row.amount : 0,
        });
      }
    }

    return Array.from(byCourse.values());
  }
}

module.exports = ReportService;
