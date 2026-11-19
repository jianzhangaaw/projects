package com.recruit_resume.service;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.options.Margin;
import com.microsoft.playwright.options.WaitUntilState;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.config.ResumePdfProperties;
import org.springframework.stereotype.Service;

@Service
public class PlaywrightPdfService {

    private final ResumePdfProperties properties;

    public PlaywrightPdfService(ResumePdfProperties properties) {
        this.properties = properties;
    }

    public byte[] generatePdf(String html) {
        try (Playwright playwright = Playwright.create();
             Browser browser = playwright.chromium().launch(new BrowserType.LaunchOptions().setHeadless(true))) {
            Page page = browser.newPage();
            page.setContent(html, new Page.SetContentOptions()
                    .setWaitUntil(WaitUntilState.NETWORKIDLE)
                    .setTimeout(properties.getRenderTimeoutSeconds() * 1000.0));
            return page.pdf(new Page.PdfOptions()
                    .setFormat("A4")
                    .setPrintBackground(true)
                    .setPreferCSSPageSize(true)
                    .setMargin(new Margin()
                            .setTop("0")
                            .setRight("0")
                            .setBottom("0")
                            .setLeft("0")));
        } catch (RuntimeException ex) {
            throw new BusinessException("Resume PDF generation failed. Please try again later.");
        }
    }
}
